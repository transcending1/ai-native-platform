# Vue3 Frontend Helm Chart

这个 Helm Chart 用于部署 Vue3 前端应用，使用 Nginx 提供静态文件服务。

## 特性

- **静态文件服务**: 使用 Nginx 提供高性能静态文件服务
- **多阶段构建**: Docker 多阶段构建优化镜像大小
- **固定副本数**: 固定运行2个Pod副本
- **健康检查**: 配置了 liveness 和 readiness 探针
- **Gzip 压缩**: 启用 Gzip 压缩提高传输效率
- **安全头**: 配置了安全相关的 HTTP 头

## 前置要求

- Kubernetes 1.19+
- Helm 3.2.0+
- Nginx Ingress Controller (如果启用 Ingress)

## 安装

### 1. 构建 Docker 镜像

```bash
cd new_web
docker build -t vue-frontend:latest .
```

### 2. 部署应用

```bash
helm install vue-frontend ./helm
```

## 配置

### 主要配置参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `vue.replicaCount` | Pod 副本数 | `2` |
| `vue.image.repository` | 镜像仓库 | `vue-frontend` |
| `vue.image.tag` | 镜像标签 | `latest` |
| `vue.autoscaling.enabled` | 启用自动扩缩容 | `true` |
| `vue.autoscaling.minReplicas` | 最小副本数 | `2` |
| `vue.autoscaling.maxReplicas` | 最大副本数 | `10` |

### 自动扩缩容配置

```yaml
vue:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80
```

### Ingress 配置

```yaml
vue:
  ingress:
    enabled: true
    className: "nginx"
    hosts:
      - host: frontend.example.com
        paths:
          - path: /
            pathType: Prefix
```

## 升级

```bash
helm upgrade vue-frontend ./helm
```

## 卸载

```bash
helm uninstall vue-frontend
```

## 故障排除

### 查看 Pod 状态

```bash
kubectl get pods -l app.kubernetes.io/name=vue-frontend
```

### 查看日志

```bash
kubectl logs -l app.kubernetes.io/name=vue-frontend
```

### 测试健康检查

```bash
curl http://frontend.example.com/health
```

### 查看 Nginx 配置

```bash
kubectl exec -it <pod-name> -- cat /etc/nginx/nginx.conf
``` 