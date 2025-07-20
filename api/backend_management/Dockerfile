FROM 955466075186.dkr.ecr.cn-northwest-1.amazonaws.com.cn/base/python:python3.11

USER root
WORKDIR /app/src
COPY --chown=root:root backend_management/ /app/src

RUN pip install --upgrade pip && pip install -r /app/src/requirements.txt\
    -i http://pypi.nexus.zhihuiya.com/repository/pypi-group/simple --trusted-host pypi.nexus.zhihuiya.com

EXPOSE 8001

CMD ["python", "./manage.py", "runserver", "0.0.0.0:8001"]
