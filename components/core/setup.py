# setup.py

import os
from setuptools import setup, find_packages

# 读取 README.md 内容，作为 PyPI 上的文档说明
def readme():
    if os.path.exists("README.md"):
        with open("README.md", encoding="utf-8") as f:
            return f.read()
    return ""

setup(
    name="ai-native-core",             # PyPI 上的发布名
    version="0.0.3",              # 版本
    description="A LLMOps Platform's native core",
    long_description=readme(),
    long_description_content_type="text/markdown",
    author="Tangyuan",
    author_email="17348241417@163.com",
    # url="https://github.com/your_repo/mlops_sdk",
    packages=find_packages(),     # 自动查找所有包
    install_requires=[
        "langchain",
        "langchain-openai",
        "langchain-community",
        "langchain-weaviate",
        "langgraph",
        "allure-pytest",
        "redis",
        "tang-yuan-mlops-sdk",
        "langchain-mcp-adapters",
        "python-dotenv",
        # 如果有其他依赖，也在此处增加
    ],
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
)