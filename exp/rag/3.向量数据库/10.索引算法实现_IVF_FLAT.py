import asyncio
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Dict, Tuple
import time
from tang_yuan_mlops_sdk.llm.embedding import EmbeddingClient
from settings import embedding_token


class IVF_FLAT_Index:
    """
    IVF_FLAT - 倒排文件索引实现
    使用k-means聚类将向量空间分割，每个聚类维护一个倒排列表
    """

    def __init__(self, nlist: int = 3, nprobe: int = 1):
        """
        初始化IVF_FLAT索引

        Args:
            nlist: 聚类数量（倒排列表数量）
            nprobe: 查询时搜索的聚类数量
        """
        self.nlist = nlist  # 聚类数量
        self.nprobe = nprobe  # 查询时搜索的聚类数量
        self.dimension = None  # 向量维度
        self.centroids = None  # 聚类中心
        self.inverted_lists = {}  # 倒排列表：{cluster_id: [(vector_id, vector), ...]}
        self.kmeans = None  # k-means模型
        self.is_trained = False

    def train(self, vectors: np.ndarray):
        """
        训练索引：对向量进行聚类，生成聚类中心

        Args:
            vectors: 训练向量，shape=(n_vectors, dimension)
        """
        print(f"开始训练IVF_FLAT索引，向量数量: {len(vectors)}, 聚类数量: {self.nlist}")

        self.dimension = vectors.shape[1]

        # 使用k-means进行聚类
        self.kmeans = KMeans(n_clusters=self.nlist, random_state=42, n_init=10)
        cluster_labels = self.kmeans.fit_predict(vectors)
        self.centroids = self.kmeans.cluster_centers_

        # 初始化倒排列表
        for i in range(self.nlist):
            self.inverted_lists[i] = []

        print(f"聚类完成，聚类中心: {self.centroids.shape}")
        self.is_trained = True

    def add_vectors(self, vectors: np.ndarray, vector_ids: List[int]):
        """
        添加向量到索引中

        Args:
            vectors: 要添加的向量，shape=(n_vectors, dimension)
            vector_ids: 向量对应的ID列表
        """
        if not self.is_trained or self.kmeans is None:
            raise ValueError("索引尚未训练，请先调用train()方法")

        print(f"添加 {len(vectors)} 个向量到索引中...")

        # 为每个向量分配到最近的聚类
        cluster_labels = self.kmeans.predict(vectors)

        # 将向量添加到对应的倒排列表中
        for i, (vector, vector_id) in enumerate(zip(vectors, vector_ids)):
            cluster_id = cluster_labels[i]
            self.inverted_lists[cluster_id].append((vector_id, vector))

        # 打印每个聚类的向量数量
        for cluster_id in range(self.nlist):
            count = len(self.inverted_lists[cluster_id])
            print(f"聚类 {cluster_id}: {count} 个向量")

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """
        搜索最相似的k个向量

        Args:
            query_vector: 查询向量，shape=(dimension,)
            k: 返回的结果数量

        Returns:
            List[Tuple[int, float]]: [(vector_id, distance), ...] 按距离升序排列
        """
        if not self.is_trained:
            raise ValueError("索引尚未训练，请先调用train()方法")

        print(f"开始搜索，nprobe={self.nprobe}, k={k}")

        # 计算查询向量与所有聚类中心的距离
        centroid_distances = np.linalg.norm(self.centroids - query_vector, axis=1)

        # 选择最近的nprobe个聚类
        nearest_clusters = np.argsort(centroid_distances)[:self.nprobe]
        print(f"选择搜索的聚类: {nearest_clusters}")

        # 在选定的聚类中搜索
        candidates = []
        for cluster_id in nearest_clusters:
            cluster_vectors = self.inverted_lists[cluster_id]
            print(f"在聚类 {cluster_id} 中搜索，包含 {len(cluster_vectors)} 个向量")

            for vector_id, vector in cluster_vectors:
                # 计算余弦相似度（距离=1-相似度，越小越相似）
                norm_vector = np.linalg.norm(vector)
                norm_query = np.linalg.norm(query_vector)
                if norm_vector == 0 or norm_query == 0:
                    # 防止除以零
                    cosine_distance = 1.0
                else:
                    cosine_similarity = np.dot(vector, query_vector) / (norm_vector * norm_query)
                    cosine_distance = 1 - cosine_similarity
                candidates.append((vector_id, cosine_distance))

        # 按距离排序并返回前k个结果
        candidates.sort(key=lambda x: x[1])
        return candidates[:k]

    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        if not self.is_trained:
            return {"status": "未训练"}

        total_vectors = sum(len(lst) for lst in self.inverted_lists.values())
        cluster_sizes = [len(self.inverted_lists[i]) for i in range(self.nlist)]

        return {
            "status": "已训练",
            "聚类数量": self.nlist,
            "向量总数": total_vectors,
            "向量维度": self.dimension,
            "搜索聚类数": self.nprobe,
            "各聚类大小": cluster_sizes,
            "平均聚类大小": np.mean(cluster_sizes),
            "聚类大小标准差": np.std(cluster_sizes)
        }


async def main():
    """主函数：演示IVF_FLAT索引的使用"""

    # 候选数据
    candidates = [
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

    print("=" * 60)
    print("IVF_FLAT 倒排文件索引算法演示")
    print("=" * 60)

    # 初始化Embedding客户端
    client = EmbeddingClient(base_url="http://222.186.32.152:10001", token=embedding_token)

    # 提取描述文本并获取embedding
    texts = [candidate["description"] for candidate in candidates]
    candidate_ids = [candidate["id"] for candidate in candidates]
    candidate_names = [candidate["name"] for candidate in candidates]

    print("正在获取embedding向量...")
    start_time = time.time()
    embeddings = await client.get_embeddings(texts)
    embedding_time = time.time() - start_time
    print(f"embedding获取完成，耗时: {embedding_time:.2f}秒")
    print(f"向量维度: {len(embeddings[0])}")

    # 转换为numpy数组
    vectors = np.array(embeddings)
    print(f"向量数据形状: {vectors.shape}")

    # 创建IVF_FLAT索引
    # 由于数据量较小，使用3个聚类，搜索时检查1个聚类
    index = IVF_FLAT_Index(nlist=3, nprobe=1)

    # 训练索引
    print("\n" + "=" * 40)
    print("训练索引")
    print("=" * 40)
    start_time = time.time()
    index.train(vectors)
    train_time = time.time() - start_time
    print(f"训练完成，耗时: {train_time:.4f}秒")

    # 添加向量到索引
    print("\n" + "=" * 40)
    print("添加向量到索引")
    print("=" * 40)
    start_time = time.time()
    index.add_vectors(vectors, candidate_ids)
    add_time = time.time() - start_time
    print(f"添加完成，耗时: {add_time:.4f}秒")

    # 显示索引统计信息
    print("\n" + "=" * 40)
    print("索引统计信息")
    print("=" * 40)
    stats = index.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # 测试查询
    test_queries = [
        "我希望找一个温柔体贴的软件工程师",
        "寻找喜欢艺术和音乐的伴侣",
        "想找一个博学的知识分子",
        "希望找一个有创意的设计师"
    ]

    print("\n" + "=" * 60)
    print("查询测试")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n查询 {i}: {query}")
        print("-" * 50)

        # 获取查询向量的embedding
        start_time = time.time()
        query_embeddings = await client.get_embeddings([query])
        query_vector = np.array(query_embeddings[0])
        embedding_time = time.time() - start_time

        # 执行搜索
        start_time = time.time()
        results = index.search(query_vector, k=3)
        search_time = time.time() - start_time

        print(f"Embedding耗时: {embedding_time:.4f}秒, 搜索耗时: {search_time:.4f}秒")
        print("搜索结果:")

        for rank, (vector_id, distance) in enumerate(results, 1):
            # 找到对应的候选人信息
            candidate = next(c for c in candidates if c["id"] == vector_id)
            similarity = 1 / (1 + distance)  # 将距离转换为相似度
            print(f"  {rank}. {candidate['name']} (ID: {vector_id})")
            print(f"     距离: {distance:.4f}, 相似度: {similarity:.4f}")
            print(f"     描述: {candidate['description']}")
            print()

    # 性能对比：IVF索引 vs 暴力搜索
    print("\n" + "=" * 60)
    print("性能对比：IVF索引 vs 暴力搜索")
    print("=" * 60)

    query = "我希望找一个温柔体贴的软件工程师"
    query_embeddings = await client.get_embeddings([query])
    query_vector = np.array(query_embeddings[0])

    # IVF搜索
    start_time = time.time()
    ivf_results = index.search(query_vector, k=3)
    ivf_time = time.time() - start_time

    # 暴力搜索
    start_time = time.time()
    distances = []
    for i, vector in enumerate(vectors):
        distance = np.linalg.norm(vector - query_vector)
        distances.append((candidate_ids[i], distance))
    distances.sort(key=lambda x: x[1])
    brute_results = distances[:3]
    brute_time = time.time() - start_time

    print(f"IVF搜索耗时: {ivf_time:.6f}秒")
    print(f"暴力搜索耗时: {brute_time:.6f}秒")
    print(f"速度提升: {brute_time / ivf_time:.2f}x")

    print("\nIVF搜索结果:")
    for rank, (vector_id, distance) in enumerate(ivf_results, 1):
        candidate = next(c for c in candidates if c["id"] == vector_id)
        print(f"  {rank}. {candidate['name']} (距离: {distance:.4f})")

    print("\n暴力搜索结果:")
    for rank, (vector_id, distance) in enumerate(brute_results, 1):
        candidate = next(c for c in candidates if c["id"] == vector_id)
        print(f"  {rank}. {candidate['name']} (距离: {distance:.4f})")

    # 验证结果一致性
    ivf_ids = [r[0] for r in ivf_results]
    brute_ids = [r[0] for r in brute_results]
    accuracy = len(set(ivf_ids) & set(brute_ids)) / len(brute_ids)
    print(f"\n结果准确率: {accuracy:.2%}")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
