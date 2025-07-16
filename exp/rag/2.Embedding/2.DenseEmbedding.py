import asyncio
from typing import List, Dict

import numpy as np
from tang_yuan_mlops_sdk.llm.embedding import EmbeddingClient

from settings import embedding_token

client = EmbeddingClient(base_url="http://222.186.32.152:10001", token=embedding_token)

texts = ["Deep Learning is not...", "Deep learning is..."]


class MatchmakingSystem:
    """相亲匹配系统"""

    def __init__(self, embedding_client):
        self.embedding_client = embedding_client
        # 模拟相亲对象数据库
        self.candidates = [
            {
                "id": 1,
                "name": "小雅",
                "description": "25岁，软件工程师，喜欢阅读和旅行，性格温柔体贴，身高165cm，爱好健身和美食，希望找一个有上进心的男生"
            },
            {
                "id": 2,
                "name": "晓琳",
                "description": "28岁，金融分析师，热爱音乐和艺术，性格开朗活泼，身高168cm，喜欢户外运动，寻找志同道合的伴侣"
            },
            {
                "id": 3,
                "name": "小慧",
                "description": "26岁，医生，温文尔雅，喜欢看书和烹饪，身高162cm，性格内敛稳重，希望找一个成熟稳重的男生"
            },
            {
                "id": 4,
                "name": "佳佳",
                "description": "24岁，设计师，充满创意和想象力，喜欢绘画和摄影，身高170cm，性格独立自信，寻找有艺术气质的伴侣"
            },
            {
                "id": 5,
                "name": "小蒙",
                "description": "27岁，教师，善良耐心，喜欢孩子和小动物，身高164cm，性格温和亲切，希望找一个有责任心的男生"
            },
            {
                "id": 6,
                "name": "欣欣",
                "description": "29岁，律师，聪明能干，喜欢辩论和思考，身高166cm，性格坚强独立，寻找智慧和幽默的伴侣"
            },
            {
                "id": 7,
                "name": "小丽",
                "description": "23岁，市场营销，外向健谈，喜欢社交和运动，身高167cm，性格活泼开朗，希望找一个阳光积极的男生"
            },
            {
                "id": 8,
                "name": "雨桐",
                "description": "30岁，研究员，博学深思，喜欢科学和读书，身高163cm，性格安静内敛，寻找有共同话题的知识分子"
            }
        ]

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)

        dot_product = np.dot(vec1_array, vec2_array)
        norm1 = np.linalg.norm(vec1_array)
        norm2 = np.linalg.norm(vec2_array)

        if norm1 == 0 or norm2 == 0:
            return 0

        return dot_product / (norm1 * norm2)

    async def find_matches(self, user_requirement: str, top_k: int = 3) -> List[Dict]:
        """
        根据用户需求找到最匹配的相亲对象
        
        Args:
            user_requirement: 用户对相亲对象的需求描述
            top_k: 返回前k个最匹配的结果
            
        Returns:
            匹配结果列表，包含相似度分数
        """
        print(f"\n🔍 正在分析您的需求: {user_requirement}")

        # 准备文本列表：用户需求 + 所有候选人描述
        texts = [user_requirement] + [candidate["description"] for candidate in self.candidates]

        # 获取所有文本的embedding
        print("📊 正在计算文本向量...")
        embeddings = await self.embedding_client.get_embeddings(texts)

        # 用户需求的embedding
        user_embedding = embeddings[0]

        # 计算相似度
        similarities = []
        for i, candidate in enumerate(self.candidates):
            candidate_embedding = embeddings[i + 1]  # +1因为第0个是用户需求
            similarity = self.cosine_similarity(user_embedding, candidate_embedding)
            similarities.append({
                "candidate": candidate,
                "similarity": similarity
            })

        # 按相似度排序并返回top_k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]

    def display_results(self, matches: List[Dict], user_requirement: str):
        """显示匹配结果"""
        print(f"\n💕 基于您的需求: '{user_requirement}'")
        print("=" * 60)
        print("为您推荐以下相亲对象:\n")

        for i, match in enumerate(matches, 1):
            candidate = match["candidate"]
            similarity = match["similarity"]

            print(f"🌟 推荐 #{i}")
            print(f"姓名: {candidate['name']}")
            print(f"介绍: {candidate['description']}")
            print(f"匹配度: {similarity:.4f} ({similarity * 100:.2f}%)")
            print("-" * 50)


async def main_with_real_api():
    """使用真实API的主程序"""
    # 初始化真实Embedding客户端
    # 初始化匹配系统
    system = MatchmakingSystem(client)

    print("🎯 相亲匹配系统 (真实API版本)")
    print("=" * 45)

    # 测试一个需求
    # test_requirement = "我希望找一个温柔体贴的女生，最好是医生或者教师，喜欢安静的生活"
    test_requirement = "我希望找一个程序员妹子"

    matches = await system.find_matches(test_requirement, top_k=3)
    system.display_results(matches, test_requirement)


if __name__ == "__main__":
    print("🚀 相亲匹配系统启动")
    asyncio.run(main_with_real_api())
