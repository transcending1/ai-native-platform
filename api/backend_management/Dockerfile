FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖
ARG APT_MIRROR=http://mirrors.tuna.tsinghua.edu.cn/

ARG DEPENDENCIES="                    \
        postgresql-client             \
        build-essential               \
        libpq-dev"

RUN set -ex \
    && sed -i "s@http://.*.debian.org@${APT_MIRROR}@g" /etc/apt/sources.list.d/debian.sources \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && apt-get update > /dev/null \
    && apt-get -y install --no-install-recommends ${DEPENDENCIES} \
    && echo "no" | dpkg-reconfigure dash \
    && apt-get clean all \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件并安装Python依赖
COPY requirements.txt /app/
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制项目文件
COPY . /app/

# 创建非root用户
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# 收集静态文件（使用构建专用设置）
ENV DJANGO_SETTINGS_MODULE=llm_api.settings.build_settings
RUN python manage.py collectstatic --noinput

# 重置为生产环境设置
ENV DJANGO_SETTINGS_MODULE=llm_api.settings.dev_settings

# 暴露端口
EXPOSE 8000

# 使用gunicorn启动应用
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync", "--timeout", "120", "--max-requests", "1000", "--max-requests-jitter", "100", "llm_api.wsgi:application"]