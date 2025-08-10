# 构建阶段
FROM node:18-alpine as build-stage

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine as production-stage

# 安装envsubst工具 (用于环境变量替换)
RUN apk add --no-cache gettext

# 复制自定义nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 复制构建的静态文件到nginx目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制docker入口脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 创建非root用户
RUN getent group nginx || addgroup -g 1001 -S nginx && \
    getent passwd nginx || adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# 设置权限 - 确保nginx用户可以写入配置文件
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    chmod 664 /usr/share/nginx/html/config.js

RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

# 暴露端口
EXPOSE 8080

# 使用入口脚本启动
ENTRYPOINT ["/docker-entrypoint.sh"]