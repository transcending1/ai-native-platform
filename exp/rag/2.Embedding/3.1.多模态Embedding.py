import base64
import json
import os
import numpy as np
from typing import List, Dict, Optional

import requests

from settings import multi_model_embedding_url

# API服务器地址
API_BASE_URL = multi_model_embedding_url

# 候选相亲对象数据
candidates = [
    {
        "id": 1,
        "name": "小雅",
        "description": "25岁，软件工程师，喜欢阅读和旅行，性格温柔体贴，身高165cm，爱好健身和美食，希望找一个有上进心的男生",
        "image": "./imgs/小雅.png"
    },
    {
        "id": 2,
        "name": "晓琳",
        "description": "28岁，金融分析师，热爱音乐和艺术，性格开朗活泼，身高168cm，喜欢户外运动，寻找志同道合的伴侣",
        "image": "./imgs/晓琳.png"
    },
    {
        "id": 3,
        "name": "小慧",
        "description": "26岁，医生，温文尔雅，喜欢看书和烹饪，身高162cm，性格内敛稳重，希望找一个成熟稳重的男生",
        "image": "./imgs/小慧.png"
    },
    {
        "id": 4,
        "name": "佳佳",
        "description": "24岁，设计师，充满创意和想象力，喜欢绘画和摄影，身高170cm，性格独立自信，寻找有艺术气质的伴侣",
        "image": "./imgs/佳佳.png"
    },
    {
        "id": 5,
        "name": "小蒙",
        "description": "27岁，教师，善良耐心，喜欢孩子和小动物，身高164cm，性格温和亲切，希望找一个有责任心的男生",
        "image": "./imgs/小蒙.png"
    },
    {
        "id": 6,
        "name": "欣欣",
        "description": "29岁，律师，聪明能干，喜欢辩论和思考，身高166cm，性格坚强独立，寻找智慧和幽默的伴侣",
        "image": "./imgs/欣欣.png"
    },
    {
        "id": 7,
        "name": "小丽",
        "description": "23岁，市场营销，外向健谈，喜欢社交和运动，身高167cm，性格活泼开朗，希望找一个阳光积极的男生",
        "image": "./imgs/小丽.png"
    },
    {
        "id": 8,
        "name": "雨桐",
        "description": "30岁，研究员，博学深思，喜欢科学和读书，身高163cm，性格安静内敛，寻找有共同话题的知识分子",
        "image": "./imgs/雨桐.png"
    }
]


def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为base64字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_embedding(data: List[Dict]) -> List[List[float]]:
    """调用API获取embedding向量"""
    try:
        response = requests.post(f"{API_BASE_URL}/embed", json={
            "inputs": data
        })
        response.raise_for_status()
        return response.json()['embeddings']
    except Exception as e:
        print(f"获取embedding失败: {e}")
        return []


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算余弦相似度"""
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    if norm1 == 0 or norm2 == 0:
        return 0
    
    return dot_product / (norm1 * norm2)


class MatchmakingSystem:
    """多模态相亲匹配系统"""
    
    def __init__(self):
        self.candidates_embeddings = {}
        self.embeddings_file = "candidates_embeddings.json"
    
    def generate_candidates_embeddings(self, force_refresh: bool = False):
        """为所有候选人生成embedding向量"""
        if not force_refresh and os.path.exists(self.embeddings_file):
            print("📚 从缓存加载候选人embedding向量...")
            with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                self.candidates_embeddings = json.load(f)
            return
        
        print("🚀 正在为所有候选人生成embedding向量...")
        
        for candidate in candidates:
            print(f"  处理候选人: {candidate['name']}")
            
            # 准备多模态数据
            image_base64 = encode_image_to_base64(candidate['image'])
            multimodal_data = [{
                "text": candidate['description'],
                "image": f"data:image/png;base64,{image_base64}"
            }]
            
            # 获取embedding
            embedding = get_embedding(multimodal_data)
            if embedding:
                self.candidates_embeddings[str(candidate['id'])] = {
                    'name': candidate['name'],
                    'description': candidate['description'],
                    'embedding': embedding[0]
                }
        
        # 保存到文件
        with open(self.embeddings_file, 'w', encoding='utf-8') as f:
            json.dump(self.candidates_embeddings, f, ensure_ascii=False, indent=2)
        
        print("✅ 候选人embedding向量生成完成！")
    
    def process_user_query(self, text_requirement: str, image_path: Optional[str] = None):
        """处理用户查询（文字需求 + 可选图片）"""
        print(f"🔍 处理用户需求...")
        print(f"  文字需求: {text_requirement}")
        
        if image_path:
            full_image_path = f"./to_query_imgs/{image_path}"
            print(f"  参考图片: {image_path}")
            
            if not os.path.exists(full_image_path):
                print(f"❌ 图片文件不存在: {full_image_path}")
                return None
            
            # 多模态查询
            image_base64 = encode_image_to_base64(full_image_path)
            query_data = [{
                "text": text_requirement,
                "image": f"data:image/png;base64,{image_base64}"
            }]
        else:
            # 纯文字查询
            query_data = [{
                "text": text_requirement
            }]
        
        # 获取查询向量
        query_embedding = get_embedding(query_data)
        if not query_embedding:
            print("❌ 获取查询embedding失败")
            return None
        
        return query_embedding[0]
    
    def find_matches(self, query_embedding: List[float], top_k: int = 3):
        """根据embedding向量找到最匹配的候选人"""
        similarities = []
        
        for candidate_id, candidate_data in self.candidates_embeddings.items():
            similarity = cosine_similarity(query_embedding, candidate_data['embedding'])
            similarities.append({
                'id': int(candidate_id),
                'name': candidate_data['name'],
                'description': candidate_data['description'],
                'similarity': similarity
            })
        
        # 按相似度排序
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def match(self, text_requirement: str, image_path: Optional[str] = None, top_k: int = 3):
        """完整的匹配流程"""
        print("💕 欢迎使用AI智能相亲匹配系统！")
        print("=" * 50)
        
        # 确保候选人embedding已生成
        if not self.candidates_embeddings:
            self.generate_candidates_embeddings()
        
        # 处理用户查询
        query_embedding = self.process_user_query(text_requirement, image_path)
        if query_embedding is None:
            return
        
        # 找到匹配结果
        matches = self.find_matches(query_embedding, top_k)
        
        # 展示结果
        self.display_results(text_requirement, image_path, matches)
    
    def display_results(self, text_requirement: str, image_path: Optional[str], matches: List[Dict]):
        """展示匹配结果"""
        print("\n🎯 匹配结果：")
        print("-" * 40)
        
        for i, match in enumerate(matches, 1):
            similarity_percent = match['similarity'] * 100
            stars = "⭐" * min(5, int(similarity_percent / 20))
            
            print(f"\n第{i}名: {match['name']} {stars}")
            print(f"匹配度: {similarity_percent:.1f}%")
            print(f"简介: {match['description']}")
            print("-" * 40)
        
        print(f"\n💌 根据您的需求 \"{text_requirement}\"", end="")
        if image_path:
            print(f" 和参考图片 \"{image_path}\"", end="")
        print("，为您推荐了以上最佳匹配！")


def run_demo():
    """运行教学演示案例"""
    system = MatchmakingSystem()
    
    print("🎉 多模态相亲匹配系统 - 教学演示")
    print("=" * 60)
    
    # 生成候选人embedding（首次运行）
    system.generate_candidates_embeddings()
    
    print("\n💡 让我们来看几个有趣的匹配案例！")
    
    # 案例1：纯文字需求
    print("\n" + "="*60)
    print("📝 案例1：纯文字需求匹配")
    system.match(
        text_requirement="我希望找一个知性优雅、喜欢读书学习的女生，最好是从事教育或医疗相关工作",
        top_k=3
    )
    
    # 案例2：文字 + 图片需求
    print("\n" + "="*60)
    print("🖼️ 案例2：多模态匹配（文字 + 图片偏好）")
    system.match(
        text_requirement="我喜欢活泼开朗、热爱运动的女生",
        image_path="1.png",  # 用户可以指定偏好的外貌类型
        top_k=3
    )
    
    # 案例3：艺术气质匹配
    print("\n" + "="*60)
    print("🎨 案例3：寻找艺术伴侣")
    system.match(
        text_requirement="",
        image_path="3.png",
        top_k=3
    )


if __name__ == '__main__':
    # 运行教学演示
    run_demo()
    
    print("\n" + "="*60)
    print("🛠️ 如何使用这个系统：")
    print("1. 系统会自动为所有候选人生成多模态embedding向量")
    print("2. 用户可以输入文字需求描述理想对象")
    print("3. 可选择上传参考图片（放在to_query_imgs目录下）")
    print("4. 系统通过余弦相似度计算匹配度")
    print("5. 返回最匹配的top-k个候选人")
    print("\n💕 祝您早日找到心仪的另一半！")
