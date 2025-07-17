import base64

import requests
from settings import multi_model_embedding_url

# API服务器地址
API_BASE_URL = multi_model_embedding_url


def encode_image_to_base64(image_path):
    """将图片文件编码为base64字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def test_text_embedding():
    """测试纯文本嵌入"""
    print("=== 测试纯文本嵌入 ===")

    data = {
        "inputs": [
            "这是一个测试文本",
            "另一个测试文本样例"
        ]
    }

    response = requests.post(f"{API_BASE_URL}/embed", json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"成功获取嵌入向量，数量: {result['count']}")
        print(f"向量维度: {result['dimensions']}")
        print(f"第一个向量前5维: {result['embeddings'][0][:5]}")
    else:
        print(f"请求失败: {response.status_code}, {response.text}")


def test_image_embedding():
    """测试纯图片嵌入（使用图片路径）"""
    print("\n=== 测试纯图片嵌入 ===")

    data = {
        "inputs": [
            {
                "image": "./imgs/cir_query.png"  # 假设图片路径存在
            },
            {
                "image": "./imgs/cir_candi_1.png"
            }
        ]
    }

    response = requests.post(f"{API_BASE_URL}/embed", json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"成功获取图片嵌入向量，数量: {result['count']}")
        print(f"向量维度: {result['dimensions']}")
        print(f"第一个向量前5维: {result['embeddings'][0][:5]}")
    else:
        print(f"请求失败: {response.status_code}, {response.text}")


def test_multimodal_embedding():
    """测试混合文本和图片嵌入"""
    print("\n=== 测试混合嵌入 ===")

    data = {
        "inputs": [
            {
                "text": "Make the background dark, as if the camera has taken the photo at night",
                "image": "./imgs/cir_query.png"
            },
            {
                "text": "描述这张图片的内容",
                "image": "./imgs/cir_candi_1.png"
            }
        ]
    }

    response = requests.post(f"{API_BASE_URL}/embed", json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"成功获取混合嵌入向量，数量: {result['count']}")
        print(f"向量维度: {result['dimensions']}")
        print(f"第一个向量前5维: {result['embeddings'][0][:5]}")
    else:
        print(f"请求失败: {response.status_code}, {response.text}")


def test_base64_image_embedding():
    """测试base64图片嵌入"""
    print("\n=== 测试Base64图片嵌入 ===")

    try:
        # 假设有一个测试图片
        image_path = "./imgs/cir_query.png"
        base64_image = encode_image_to_base64(image_path)

        data = {
            "inputs": [
                {
                    "image": f"data:image/png;base64,{base64_image}"
                },
                {
                    "text": "这是base64编码的图片",
                    "image": f"data:image/png;base64,{base64_image}"
                }
            ]
        }

        response = requests.post(f"{API_BASE_URL}/embed", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"成功获取Base64图片嵌入向量，数量: {result['count']}")
            print(f"向量维度: {result['dimensions']}")
            print(f"第一个向量前5维: {result['embeddings'][0][:5]}")
        else:
            print(f"请求失败: {response.status_code}, {response.text}")

    except FileNotFoundError:
        print("测试图片文件不存在，跳过Base64测试")


def test_mixed_inputs():
    """测试混合输入类型"""
    print("\n=== 测试混合输入类型 ===")

    data = {
        "inputs": [
            "纯文本输入",
            {
                "text": "只有文本"
            },
            {
                "image": "./imgs/cir_query.png"  # 只有图片
            },
            {
                "text": "文本和图片组合",
                "image": "./imgs/cir_candi_1.png"
            }
        ]
    }

    response = requests.post(f"{API_BASE_URL}/embed", json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"成功获取混合输入嵌入向量，数量: {result['count']}")
        print(f"向量维度: {result['dimensions']}")
        for i, emb in enumerate(result['embeddings']):
            print(f"第{i + 1}个向量前3维: {emb[:3]}")
    else:
        print(f"请求失败: {response.status_code}, {response.text}")


def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")

    response = requests.get(f"{API_BASE_URL}/health")
    if response.status_code == 200:
        result = response.json()
        print(f"服务状态: {result['status']}")
        print(f"模型已加载: {result['model_loaded']}")
    else:
        print(f"健康检查失败: {response.status_code}, {response.text}")


def main():
    """主函数，运行所有测试"""
    print("多模态Embedding API客户端测试")
    print("=" * 50)

    # 首先检查服务是否正常
    try:
        test_health_check()
    except requests.exceptions.ConnectionError:
        print("无法连接到API服务器，请确保Flask应用正在运行")
        return

    # 运行各种测试
    test_text_embedding()
    test_image_embedding()
    test_multimodal_embedding()
    test_base64_image_embedding()
    test_mixed_inputs()


if __name__ == "__main__":
    main()
