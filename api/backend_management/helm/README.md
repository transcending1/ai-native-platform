# Django Backend Helm Chart

这个 Helm Chart 用于部署 Django 后端应用，包含 PostgreSQL 和 Redis 依赖服务。

## 特性

- **多进程部署**: 使用 Gunicorn 启动多个 worker 进程
- **数据库支持**: 集成 PostgreSQL 数据库
- **缓存支持**: 集成 Redis 缓存
- **自动扩缩容**: 支持 HPA (Horizontal Pod Autoscaler)
- **健康检查**: 配置了 liveness 和 readiness 探针
- **持久化存储**: 支持媒体文件持久化存储

## 前置要求

- Kubernetes 1.19+
- Helm 3.2.0+
- Nginx Ingress Controller (如果启用 Ingress)

## 安装

### 1. 添加依赖仓库

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 2. 构建 Docker 镜像

```bash
cd api/backend_management
docker build -t django-backend:latest .
```

### 3. 部署应用

```bash
# 安装依赖
helm dependency update ./helm

# 部署到 Kubernetes
helm install django-backend ./helm
```

## 配置

### 主要配置参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `django.replicaCount` | Pod 副本数 | `2` |
| `django.image.repository` | 镜像仓库 | `django-backend` |
| `django.image.tag` | 镜像标签 | `latest` |
| `postgresql.enabled` | 启用 PostgreSQL | `true` |
| `redis.enabled` | 启用 Redis | `true` |

### 环境变量配置

应用通过以下环境变量进行配置：

- `DJANGO_SETTINGS_MODULE`: Django 设置模块
- `DATABASE_HOST`: 数据库主机
- `DATABASE_NAME`: 数据库名称
- `DATABASE_USER`: 数据库用户
- `DATABASE_PASSWORD`: 数据库密码
- `REDIS_HOST`: Redis 主机
- `REDIS_PORT`: Redis 端口

## 升级

```bash
helm upgrade django-backend ./helm
```

## 卸载

```bash
helm uninstall django-backend
```

## 故障排除

### 查看 Pod 状态

```bash
kubectl get pods -l app.kubernetes.io/name=django-backend
```

### 查看日志

```bash
kubectl logs -l app.kubernetes.io/name=django-backend
```

### 查看服务状态

```bash
kubectl get svc -l app.kubernetes.io/name=django-backend
``` 