import json
import os
import shutil
import subprocess
import zipfile

import paramiko
from django.core.management import BaseCommand


# SFTP 上传文件到远程服务器
def upload_file_to_remote(local_file, remote_file, hostname, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, password=password)

    sftp = client.open_sftp()
    sftp.put(local_file, remote_file)
    sftp.close()

    client.close()


# 执行远程命令
def execute_remote_command(command, hostname, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, password=password)

    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    client.close()

    return output, error


def download_file_to_local(local_file, remote_file, hostname, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, password=password)

    sftp = client.open_sftp()
    sftp.get(remote_file, local_file)
    sftp.close()

    client.close()


class Command(BaseCommand):
    help = '生成SDK'

    @staticmethod
    def _handle():
        # 定义 Shell 命令
        command = 'python manage.py generate_swagger swagger.json'

        # 执行 Shell 命令
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        # 打印命令执行结果
        print(result.stdout)

        # 打开原始 swagger.json 文件
        with open('swagger.json', 'r') as f:
            data = json.load(f)

        # 将数据重新编码为UTF-8
        with open('swagger.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # 本地文件路径
        local_file = 'swagger.json'

        # 远程服务器信息
        hostname = '192.168.3.237'
        port = 22
        username = 'root'
        password = 'Abc.1234'

        # 远程文件路径
        remote_file = '/home/swagger.json'

        # 上传文件到远程服务器
        upload_file_to_remote(local_file, remote_file, hostname, port, username, password)

        # 执行命令判断远程SDK文件夹是否存在,是的话就删除
        command = 'cd /home && rm -rf sdk'
        output, error = execute_remote_command(command, hostname, port, username, password)
        print("remove sdk command output: ", output)
        print("remove sdk command error: ", error)

        # 执行远程Python SDK 生成命令
        command = (
            'cd /home && docker run --rm -v ${PWD}:/local swaggerapi/swagger-codegen-cli '
            'generate -i /local/swagger.json -l python -o /local/sdk'
            ' && docker run --rm -v ${PWD}:/local swaggerapi/swagger-codegen-cli '
            'generate -i /local/swagger.json -l typescript-node -o /local/ts-sdk'
        )
        output, error = execute_remote_command(command, hostname, port, username, password)
        print("generate swagger command output: ", output)
        print("generate swagger command error: ", error)

        # 执行远程SDK压缩命令
        zip_command = (
            'cd /home/sdk && zip -r sdk.zip .'
            ' && cd /home/ts-sdk && zip -r ts-sdk.zip .'
        )
        output, error = execute_remote_command(zip_command, hostname, port, username, password)
        print("zip command output: ", output)
        print("zip command error: ", error)

        # 下载远程文件到本地
        download_file_to_local(
            '../llm_sdks/llm_python_sdk/sdk.zip', '/home/sdk/sdk.zip',
            hostname, port, username, password
        )
        download_file_to_local(
            '../llm_sdks/llm_ts_sdk/ts-sdk.zip', '/home/ts-sdk/ts-sdk.zip',
            hostname, port, username, password
        )

        with zipfile.ZipFile('../llm_sdks/llm_python_sdk/sdk.zip', 'r') as zip_ref:
            zip_ref.extractall('../llm_sdks/llm_python_sdk')

        with zipfile.ZipFile('../llm_sdks/llm_ts_sdk/ts-sdk.zip', 'r') as zip_ref:
            zip_ref.extractall('../llm_sdks/llm_ts_sdk')

    def handle(self, *args, **options):
        # remove ../llm_python_sdk/sdk folder on windows
        if os.path.exists('../llm_sdks/llm_python_sdk'):
            shutil.rmtree('../llm_sdks/llm_python_sdk')
            os.mkdir('../llm_sdks/llm_python_sdk')
        if os.path.exists('../llm_sdks/llm_ts_sdk'):
            shutil.rmtree('../llm_sdks/llm_ts_sdk')
            os.mkdir('../llm_sdks/llm_ts_sdk')
        try:
            self._handle()
        except Exception as e:
            print(e)
            self.stdout.write(self.style.ERROR('生成SDK失败'))
        finally:
            if os.path.exists('swagger.json'):
                os.remove('swagger.json')
            if os.path.exists('../llm_python_sdk/sdk.zip'):
                os.remove('../llm_python_sdk/sdk.zip')
            if os.path.exists('../llm_ts_sdk/ts-sdk.zip'):
                os.remove('../llm_ts_sdk/ts-sdk.zip')
