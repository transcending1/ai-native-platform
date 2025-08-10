#!/bin/bash

set -e

echo "🚀 AI Native Platform CI/CD流水线开始..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_ROOT=$(pwd)
BUILD_DIR="$PROJECT_ROOT/build"
TEMP_DIR="$PROJECT_ROOT/temp"
VERSION_FILE="$PROJECT_ROOT/build_version.json"

# 镜像配置
BACKEND_IMAGE_NAME="django-backend"
FRONTEND_IMAGE_NAME="vue-frontend"

# K8s命名空间
NAMESPACE="ai-platform"

# 函数：打印信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
AI Native Platform CI/CD部署脚本

用法: $0 [选项] [命令]

命令:
    build       构建镜像 [默认]
    deploy      仅部署（从OSS下载镜像）
    clean       清理临时文件
    status      显示部署状态

选项:
    --backend-only      仅处理后端
    --frontend-only     仅处理前端
    --skip-upload       跳过OSS上传
    --skip-download     跳过OSS下载
    --increment TYPE    版本递增类型 (major|minor|patch|build) [默认: build]
    --dry-run          仅显示要执行的操作，不实际执行
    -h, --help         显示帮助信息

示例:
    $0                             # 完整构建和部署流程
    $0 --backend-only              # 仅构建和部署后端
    $0 --increment minor           # 递增minor版本并构建部署
    $0 deploy --skip-upload        # 仅部署，从OSS下载镜像
    $0 clean                       # 清理临时文件

环境变量:
    OSS_BUCKET         OSS存储桶名称
    OSS_ACCESS_KEY_ID  OSS访问密钥ID
    OSS_ACCESS_KEY_SECRET  OSS访问密钥Secret
    KUBECONFIG         Kubernetes配置文件路径

EOF
}

# 检查前置条件
check_prerequisites() {
    print_info "检查前置条件..."

    local missing_tools=()

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi

    # 检查kubectl
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi

    # 检查helm
    if ! command -v helm &> /dev/null; then
        missing_tools+=("helm")
    fi

    # 检查ctr
    if ! command -v ctr &> /dev/null; then
        missing_tools+=("ctr")
    fi

    # 检查Python3
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi

    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "缺少必要工具: ${missing_tools[*]}"
        print_error "请安装缺少的工具后重试"
        exit 1
    fi

    # 检查Python依赖
    if ! python3 -c "import alibabacloud_oss_v2" &> /dev/null; then
        print_warning "缺少Python OSS SDK，尝试安装..."
        pip3 install alibabacloud-oss-v2 || {
            print_error "安装OSS SDK失败，请手动安装: pip3 install alibabacloud-oss-v2"
            exit 1
        }
    fi

    print_success "前置条件检查完成"
}

# 初始化环境
init_environment() {
    print_info "初始化构建环境..."

    # 创建必要目录
    mkdir -p "$BUILD_DIR" "$TEMP_DIR"

    # 确保脚本有执行权限
    chmod +x "$PROJECT_ROOT/version_manager.py" "$PROJECT_ROOT/oss_manager.py" 2>/dev/null || true

    print_success "环境初始化完成"
}

# 版本管理
manage_version() {
    local increment_type=${1:-"build"}

    print_info "管理版本信息..."

    if [ ! -f "$PROJECT_ROOT/version_manager.py" ]; then
        print_error "版本管理脚本不存在: version_manager.py"
        exit 1
    fi

    # 递增版本
    if [ "$increment_type" = "build" ]; then
        python3 "$PROJECT_ROOT/version_manager.py" build
    else
        python3 "$PROJECT_ROOT/version_manager.py" version --type "$increment_type"
    fi

    # 导出版本环境变量
    python3 "$PROJECT_ROOT/version_manager.py" export --output "$BUILD_DIR/version.env"
    source "$BUILD_DIR/version.env"

    print_success "版本管理完成: $BUILD_TAG"
}

# 构建后端镜像
build_backend() {
    print_info "构建Django后端镜像..."

    cd api/backend_management

    # 构建镜像，传递版本信息
    docker build \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_NUMBER="$BUILD_NUMBER" \
        --build-arg BUILD_TIMESTAMP="$BUILD_TIMESTAMP" \
        -t "${BACKEND_IMAGE_NAME}:${BUILD_TAG}" \
        -t "${BACKEND_IMAGE_NAME}:latest" \
        .

    print_success "后端镜像构建完成: ${BACKEND_IMAGE_NAME}:${BUILD_TAG}"
    cd "$PROJECT_ROOT"
}

# 构建前端镜像
build_frontend() {
    print_info "构建Vue3前端镜像..."

    cd new_web

    # 构建镜像，传递版本信息
    docker build \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_NUMBER="$BUILD_NUMBER" \
        --build-arg BUILD_TIMESTAMP="$BUILD_TIMESTAMP" \
        -t "${FRONTEND_IMAGE_NAME}:${BUILD_TAG}" \
        -t "${FRONTEND_IMAGE_NAME}:latest" \
        .

    print_success "前端镜像构建完成: ${FRONTEND_IMAGE_NAME}:${BUILD_TAG}"
    cd "$PROJECT_ROOT"
}

# 保存镜像为tar包
save_images() {
    print_info "保存镜像为tar包..."

    if [ "$BACKEND_ONLY" != true ]; then
        if [ "$FRONTEND_ONLY" != true ]; then
            # 保存后端镜像
            local backend_tar="$BUILD_DIR/${BACKEND_IMAGE_NAME}-${BUILD_TAG}.tar"
            print_info "保存后端镜像: $backend_tar"
            docker save "${BACKEND_IMAGE_NAME}:${BUILD_TAG}" -o "$backend_tar"

            # 压缩tar包以减少文件大小
            print_info "压缩镜像包..."
            gzip "$backend_tar"
            BACKEND_TAR_FILE="${backend_tar}.gz"
        fi
    fi

    if [ "$FRONTEND_ONLY" != true ]; then
        if [ "$BACKEND_ONLY" != true ]; then
            # 保存前端镜像
            local frontend_tar="$BUILD_DIR/${FRONTEND_IMAGE_NAME}-${BUILD_TAG}.tar"
            print_info "保存前端镜像: $frontend_tar"
            docker save "${FRONTEND_IMAGE_NAME}:${BUILD_TAG}" -o "$frontend_tar"

            # 压缩tar包
            gzip "$frontend_tar"
            FRONTEND_TAR_FILE="${frontend_tar}.gz"
        fi
    fi

    print_success "镜像保存完成"
}

# 上传到OSS
upload_to_oss() {
    if [ "$SKIP_UPLOAD" = true ]; then
        print_warning "跳过OSS上传"
        return
    fi

    print_info "上传镜像到OSS..."

    if [ ! -f "$PROJECT_ROOT/oss_manager.py" ]; then
        print_error "OSS管理脚本不存在: oss_manager.py"
        exit 1
    fi

    # 上传后端镜像
    if [ "$FRONTEND_ONLY" != true ] && [ -f "$BACKEND_TAR_FILE" ]; then
        print_info "上传后端镜像: $(basename "$BACKEND_TAR_FILE")"
        python3 "$PROJECT_ROOT/oss_manager.py" upload "$BACKEND_TAR_FILE" \
            --key "docker-images/backend/$(basename "$BACKEND_TAR_FILE")"
    fi

    # 上传前端镜像
    if [ "$BACKEND_ONLY" != true ] && [ -f "$FRONTEND_TAR_FILE" ]; then
        print_info "上传前端镜像: $(basename "$FRONTEND_TAR_FILE")"
        python3 "$PROJECT_ROOT/oss_manager.py" upload "$FRONTEND_TAR_FILE" \
            --key "docker-images/frontend/$(basename "$FRONTEND_TAR_FILE")"
    fi

    print_success "OSS上传完成"
}

# 从OSS下载镜像
download_from_oss() {
    if [ "$SKIP_DOWNLOAD" = true ]; then
        print_warning "跳过OSS下载"
        return
    fi

    print_info "从OSS下载镜像..."

    # 下载后端镜像
    if [ "$FRONTEND_ONLY" != true ]; then
        local backend_key="docker-images/backend/${BACKEND_IMAGE_NAME}-${BUILD_TAG}.tar.gz"
        local backend_local="$TEMP_DIR/$(basename "$backend_key")"

        print_info "下载后端镜像: $backend_key"
        python3 "$PROJECT_ROOT/oss_manager.py" download "$backend_key" --output "$backend_local"
        BACKEND_TAR_FILE="$backend_local"
    fi

    # 下载前端镜像
    if [ "$BACKEND_ONLY" != true ]; then
        local frontend_key="docker-images/frontend/${FRONTEND_IMAGE_NAME}-${BUILD_TAG}.tar.gz"
        local frontend_local="$TEMP_DIR/$(basename "$frontend_key")"

        print_info "下载前端镜像: $frontend_key"
        python3 "$PROJECT_ROOT/oss_manager.py" download "$frontend_key" --output "$frontend_local"
        FRONTEND_TAR_FILE="$frontend_local"
    fi

    print_success "OSS下载完成"
}

# 使用ctr加载镜像到K8s
load_images_to_k8s() {
    print_info "使用ctr加载镜像到Kubernetes..."

    # 解压并加载后端镜像
    if [ "$FRONTEND_ONLY" != true ] && [ -f "$BACKEND_TAR_FILE" ]; then
        print_info "加载后端镜像到containerd..."

        # 解压
        local uncompressed_backend="${BACKEND_TAR_FILE%.gz}"
        gunzip -c "$BACKEND_TAR_FILE" > "$uncompressed_backend"

        # 使用ctr导入镜像
        sudo ctr -n k8s.io images import "$uncompressed_backend"

        # 验证镜像导入
        if sudo ctr -n k8s.io images list | grep -q "$BACKEND_IMAGE_NAME"; then
            print_success "后端镜像导入成功"
        else
            print_error "后端镜像导入失败"
            exit 1
        fi

        # 清理临时文件
        rm -f "$uncompressed_backend"
    fi

    # 解压并加载前端镜像
    if [ "$BACKEND_ONLY" != true ] && [ -f "$FRONTEND_TAR_FILE" ]; then
        print_info "加载前端镜像到containerd..."

        # 解压
        local uncompressed_frontend="${FRONTEND_TAR_FILE%.gz}"
        gunzip -c "$FRONTEND_TAR_FILE" > "$uncompressed_frontend"

        # 使用ctr导入镜像
        sudo ctr -n k8s.io images import "$uncompressed_frontend"

        # 验证镜像导入
        if sudo ctr -n k8s.io images list | grep -q "$FRONTEND_IMAGE_NAME"; then
            print_success "前端镜像导入成功"
        else
            print_error "前端镜像导入失败"
            exit 1
        fi

        # 清理临时文件
        rm -f "$uncompressed_frontend"
    fi

    print_success "镜像加载完成"
}

# 部署到K8s
deploy_to_k8s() {
    print_info "部署到Kubernetes..."

    # 添加helm仓库
    print_info "更新Helm仓库..."
    helm repo add azure http://mirror.azure.cn/kubernetes/charts || true
    helm repo update

    # 部署后端
    if [ "$FRONTEND_ONLY" != true ]; then
        print_info "部署Django后端应用..."
        cd api/backend_management

        # 更新依赖
        helm dependency update ./helm --debug

        # 部署后端，传递版本信息
        helm upgrade --install django-backend ./helm \
            --namespace "$NAMESPACE" \
            --create-namespace \
            --set image.tag="$BUILD_TAG" \
            --set version="$VERSION" \
            --set buildNumber="$BUILD_NUMBER" \
            --wait \
            --timeout=600s

        print_success "后端应用部署完成"
        cd "$PROJECT_ROOT"
    fi

    # 部署前端
    if [ "$BACKEND_ONLY" != true ]; then
        print_info "部署Vue3前端应用..."
        cd new_web

        # 部署前端，传递版本信息
        helm upgrade --install vue-frontend ./helm \
            --namespace "$NAMESPACE" \
            --create-namespace \
            --set image.tag="$BUILD_TAG" \
            --set version="$VERSION" \
            --set buildNumber="$BUILD_NUMBER" \
            --wait \
            --timeout=300s

        print_success "前端应用部署完成"
        cd "$PROJECT_ROOT"
    fi

    print_success "Kubernetes部署完成"
}

# 显示部署状态
show_status() {
    print_info "查看部署状态..."

    echo ""
    echo "📋 版本信息:"
    if [ -f "$BUILD_DIR/version.env" ]; then
        source "$BUILD_DIR/version.env"
        echo "  版本: $VERSION"
        echo "  构建号: $BUILD_NUMBER"
        echo "  构建标签: $BUILD_TAG"
    fi

    echo ""
    echo "📋 Pod状态:"
    kubectl get pods -n "$NAMESPACE" -o wide

    echo ""
    echo "🔧 Service状态:"
    kubectl get svc -n "$NAMESPACE"

    echo ""
    echo "🌐 Ingress状态:"
    kubectl get ingress -n "$NAMESPACE" 2>/dev/null || echo "  无Ingress配置"

    echo ""
    echo "🐳 镜像状态:"
    sudo ctr -n k8s.io images list | grep -E "(django-backend|vue-frontend)" || echo "  未找到相关镜像"

    echo ""
    print_success "部署状态查看完成！"
    print_warning "请确保你的Kubernetes集群中已安装Nginx Ingress Controller"
}

# 清理临时文件
cleanup() {
    print_info "清理临时文件..."

    rm -rf "$TEMP_DIR"
    rm -f "$BUILD_DIR"/*.tar "$BUILD_DIR"/*.tar.gz

    print_success "清理完成"
}

# 完整构建流程
full_build() {
    init_environment
    manage_version "$INCREMENT_TYPE"

    # 构建镜像
    if [ "$FRONTEND_ONLY" != true ]; then
        build_backend
    fi

    if [ "$BACKEND_ONLY" != true ]; then
        build_frontend
    fi

    # 保存并上传镜像
    save_images
    upload_to_oss
}

# 完整部署流程
full_deploy() {
    init_environment

    # 如果有版本环境变量文件，加载它
    if [ -f "$BUILD_DIR/version.env" ]; then
        source "$BUILD_DIR/version.env"
    else
        # 如果没有，获取当前版本
        python3 "$PROJECT_ROOT/version_manager.py" export --output "$BUILD_DIR/version.env"
        source "$BUILD_DIR/version.env"
    fi

    download_from_oss
    load_images_to_k8s
    deploy_to_k8s
}

# 解析命令行参数
BACKEND_ONLY=false
FRONTEND_ONLY=false
SKIP_UPLOAD=false
SKIP_DOWNLOAD=false
INCREMENT_TYPE="build"
DRY_RUN=false
COMMAND="build"

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --skip-upload)
            SKIP_UPLOAD=true
            shift
            ;;
        --skip-download)
            SKIP_DOWNLOAD=true
            shift
            ;;
        --increment)
            INCREMENT_TYPE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        build|deploy|clean|status)
            COMMAND="$1"
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证参数
if [ "$BACKEND_ONLY" = true ] && [ "$FRONTEND_ONLY" = true ]; then
    print_error "不能同时指定 --backend-only 和 --frontend-only"
    exit 1
fi

if [[ ! "$INCREMENT_TYPE" =~ ^(major|minor|patch|build)$ ]]; then
    print_error "无效的版本递增类型: $INCREMENT_TYPE"
    print_error "支持的类型: major, minor, patch, build"
    exit 1
fi

# 如果是dry-run模式，显示将要执行的操作
if [ "$DRY_RUN" = true ]; then
    print_warning "干运行模式 - 仅显示将要执行的操作"
    echo "命令: $COMMAND"
    echo "版本递增类型: $INCREMENT_TYPE"
    echo "仅后端: $BACKEND_ONLY"
    echo "仅前端: $FRONTEND_ONLY"
    echo "跳过上传: $SKIP_UPLOAD"
    echo "跳过下载: $SKIP_DOWNLOAD"
    exit 0
fi

# 主执行流程
main() {
    print_info "=== AI Native Platform CI/CD流水线 ==="

    check_prerequisites

    case "$COMMAND" in
        build)
            print_info "执行完整构建和部署流程..."
            full_build
            full_deploy
            show_status
            ;;
        deploy)
            print_info "执行部署流程..."
            full_deploy
            show_status
            ;;
        clean)
            cleanup
            ;;
        status)
            show_status
            ;;
        *)
            print_error "未知命令: $COMMAND"
            show_help
            exit 1
            ;;
    esac

    print_success "=== CI/CD流水线执行完成 ==="
}

# 捕获错误并清理
trap 'print_error "流水线执行过程中发生错误"; cleanup' ERR

# 执行主函数
main "$@"