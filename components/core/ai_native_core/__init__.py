from dotenv import load_dotenv

# 根据环境变量 ENV 加载对应的 .env 文件
import os

env = os.getenv("ENV")
if env == "test":
    load_dotenv(".env.test")
else:
    load_dotenv()