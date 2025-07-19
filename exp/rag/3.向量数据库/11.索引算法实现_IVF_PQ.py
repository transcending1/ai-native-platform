import asyncio
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Dict, Tuple
import time
from tang_yuan_mlops_sdk.llm.embedding import EmbeddingClient
from settings import embedding_token


class ProductQuantizer:
    """
    乘积量化器 - 将高维向量分解为多个子空间并量化
    """

    def __init__(self, m: int = 4, nbits: int = 8):
        """
        初始化乘积量化器

        Args:
            m: 子空间数量，向量将被分解为m个子向量
            nbits: 每个子空间的量化位数，质心数量为2^nbits
        """
        self.m = m  # 子空间数量
        self.nbits = nbits  # 量化位数
        self.k = 2 ** nbits  # 每个子空间的质心数量
        self.dimension: int = 0  # 向量维度
        self.d_sub: int = 0  # 每个子空间的维度
        self.codebooks = []  # 每个子空间的码本（质心）
        self.is_trained = False

    def train(self, vectors: np.ndarray):
        """
        训练乘积量化器，为每个子空间生成码本

        Args:
            vectors: 训练向量，shape=(n_vectors, dimension)
        """
        print(f"开始训练乘积量化器，子空间数量: {self.m}, 每个子空间质心数: {self.k}")

        self.dimension = vectors.shape[1]
        
        # 确保维度能被子空间数量整除
        if self.dimension % self.m != 0:
            raise ValueError(f"向量维度 {self.dimension} 不能被子空间数量 {self.m} 整除")
        
        self.d_sub = self.dimension // self.m
        print(f"每个子空间维度: {self.d_sub}")

        # 为每个子空间训练码本
        self.codebooks = []
        for i in range(self.m):
            print(f"训练第 {i+1}/{self.m} 个子空间码本...")
            
            # 提取第i个子空间的向量
            start_idx = i * self.d_sub
            end_idx = (i + 1) * self.d_sub
            sub_vectors = vectors[:, start_idx:end_idx]
            
            # 使用K-means生成质心
            kmeans = KMeans(n_clusters=self.k, random_state=42, n_init='auto')
            kmeans.fit(sub_vectors)
            
            # 保存码本（质心）
            self.codebooks.append(kmeans.cluster_centers_)
            print(f"子空间 {i+1} 码本形状: {kmeans.cluster_centers_.shape}")

        self.is_trained = True
        print("乘积量化器训练完成")

    def encode(self, vectors: np.ndarray) -> np.ndarray:
        """
        将向量编码为PQ码

        Args:
            vectors: 输入向量，shape=(n_vectors, dimension)

        Returns:
            PQ码，shape=(n_vectors, m)，每个元素是子空间质心的索引
        """
        if not self.is_trained:
            raise ValueError("量化器尚未训练，请先调用train()方法")

        n_vectors = vectors.shape[0]
        codes = np.zeros((n_vectors, self.m), dtype=np.uint8)

        for i in range(self.m):
            # 提取第i个子空间的向量
            start_idx = i * self.d_sub
            end_idx = (i + 1) * self.d_sub
            sub_vectors = vectors[:, start_idx:end_idx]
            
            # 计算距离并找到最近质心
            codebook = self.codebooks[i]
            for j, sub_vector in enumerate(sub_vectors):
                distances = np.linalg.norm(codebook - sub_vector, axis=1)
                codes[j, i] = np.argmin(distances)

        return codes

    def decode(self, codes: np.ndarray) -> np.ndarray:
        """
        将PQ码解码为近似向量

        Args:
            codes: PQ码，shape=(n_vectors, m)

        Returns:
            解码向量，shape=(n_vectors, dimension)
        """
        if not self.is_trained:
            raise ValueError("量化器尚未训练，请先调用train()方法")

        n_vectors = codes.shape[0]
        decoded_vectors = np.zeros((n_vectors, self.dimension))

        for i in range(self.m):
            start_idx = i * self.d_sub
            end_idx = (i + 1) * self.d_sub
            
            for j in range(n_vectors):
                code = codes[j, i]
                decoded_vectors[j, start_idx:end_idx] = self.codebooks[i][code]

        return decoded_vectors

    def compute_distance_table(self, query_vector: np.ndarray) -> np.ndarray:
        """
        计算查询向量与所有码本质心的距离表

        Args:
            query_vector: 查询向量，shape=(dimension,)

        Returns:
            距离表，shape=(m, k)，[i, j]表示查询向量第i个子向量与第i个子空间第j个质心的距离
        """
        if not self.is_trained:
            raise ValueError("量化器尚未训练，请先调用train()方法")

        distance_table = np.zeros((self.m, self.k))

        for i in range(self.m):
            # 提取查询向量第i个子向量
            start_idx = i * self.d_sub
            end_idx = (i + 1) * self.d_sub
            query_sub_vector = query_vector[start_idx:end_idx]
            
            # 计算与第i个子空间所有质心的距离
            codebook = self.codebooks[i]
            for j in range(self.k):
                distance_table[i, j] = np.linalg.norm(query_sub_vector - codebook[j])

        return distance_table

    def estimate_distance(self, codes: np.ndarray, distance_table: np.ndarray) -> np.ndarray:
        """
        使用距离表估算PQ码向量与查询向量的距离

        Args:
            codes: PQ码，shape=(n_vectors, m)
            distance_table: 距离表，shape=(m, k)

        Returns:
            估算距离，shape=(n_vectors,)
        """
        n_vectors = codes.shape[0]
        distances = np.zeros(n_vectors)

        for i in range(n_vectors):
            # 累加每个子空间的距离平方
            distance_squared = 0
            for j in range(self.m):
                code = codes[i, j]
                distance_squared += distance_table[j, code] ** 2
            distances[i] = np.sqrt(distance_squared)

        return distances


class IVF_PQ_Index:
    """
    IVF_PQ - 倒排文件与乘积量化索引实现
    结合倒排文件索引和乘积量化的高效向量检索算法
    """

    def __init__(self, nlist: int = 3, nprobe: int = 1, m: int = 4, nbits: int = 8):
        """
        初始化IVF_PQ索引

        Args:
            nlist: 聚类数量（倒排列表数量）
            nprobe: 查询时搜索的聚类数量
            m: 乘积量化子空间数量
            nbits: 每个子空间的量化位数
        """
        self.nlist = nlist
        self.nprobe = nprobe
        self.m = m
        self.nbits = nbits
        
        self.dimension: int = 0
        self.centroids = None  # 聚类中心
        self.inverted_lists = {}  # 倒排列表：{cluster_id: [(vector_id, pq_code), ...]}
        self.kmeans = None  # k-means模型
        self.pq = ProductQuantizer(m=m, nbits=nbits)  # 乘积量化器
        self.is_trained = False

    def train(self, vectors: np.ndarray):
        """
        训练索引：进行聚类并训练乘积量化器

        Args:
            vectors: 训练向量，shape=(n_vectors, dimension)
        """
        print(f"开始训练IVF_PQ索引，向量数量: {len(vectors)}, 聚类数量: {self.nlist}")

        self.dimension = vectors.shape[1]

        # 1. 训练倒排文件索引（IVF部分）
        print("训练倒排文件索引...")
        self.kmeans = KMeans(n_clusters=self.nlist, random_state=42, n_init='auto')
        cluster_labels = self.kmeans.fit_predict(vectors)
        self.centroids = self.kmeans.cluster_centers_

        # 初始化倒排列表
        for i in range(self.nlist):
            self.inverted_lists[i] = []

        # 2. 训练乘积量化器（PQ部分）
        print("训练乘积量化器...")
        self.pq.train(vectors)

        print(f"IVF_PQ索引训练完成")
        self.is_trained = True

    def add_vectors(self, vectors: np.ndarray, vector_ids: List[int]):
        """
        添加向量到索引中

        Args:
            vectors: 要添加的向量，shape=(n_vectors, dimension)
            vector_ids: 向量对应的ID列表
        """
        if not self.is_trained:
            raise ValueError("索引尚未训练，请先调用train()方法")

        print(f"添加 {len(vectors)} 个向量到索引中...")

        # 1. 为每个向量分配到最近的聚类
        if self.kmeans is None:
            raise ValueError("K-means模型尚未训练")
        cluster_labels = self.kmeans.predict(vectors)

        # 2. 将向量编码为PQ码
        pq_codes = self.pq.encode(vectors)

        # 3. 将PQ码添加到对应的倒排列表中
        for i, (vector_id, pq_code) in enumerate(zip(vector_ids, pq_codes)):
            cluster_id = cluster_labels[i]
            self.inverted_lists[cluster_id].append((vector_id, pq_code))

        # 打印每个聚类的向量数量和压缩统计
        total_original_size = len(vectors) * self.dimension * 4  # 假设32位浮点数
        total_compressed_size = len(vectors) * self.m * (self.nbits / 8)
        compression_ratio = total_original_size / total_compressed_size

        print(f"压缩统计:")
        print(f"  原始大小: {total_original_size / 1024:.2f} KB")
        print(f"  压缩大小: {total_compressed_size / 1024:.2f} KB")
        print(f"  压缩比: {compression_ratio:.2f}x")

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

        # 1. 计算查询向量与所有聚类中心的距离
        centroid_distances = np.linalg.norm(self.centroids - query_vector, axis=1)

        # 2. 选择最近的nprobe个聚类
        nearest_clusters = np.argsort(centroid_distances)[:self.nprobe]
        print(f"选择搜索的聚类: {nearest_clusters}")

        # 3. 预计算距离表
        distance_table = self.pq.compute_distance_table(query_vector)

        # 4. 在选定的聚类中搜索
        candidates = []
        for cluster_id in nearest_clusters:
            cluster_entries = self.inverted_lists[cluster_id]
            print(f"在聚类 {cluster_id} 中搜索，包含 {len(cluster_entries)} 个向量")

            if len(cluster_entries) == 0:
                continue

            # 提取PQ码
            vector_ids = [entry[0] for entry in cluster_entries]
            pq_codes = np.array([entry[1] for entry in cluster_entries])

            # 使用距离表估算距离
            distances = self.pq.estimate_distance(pq_codes, distance_table)

            # 添加到候选列表
            for vector_id, distance in zip(vector_ids, distances):
                candidates.append((vector_id, distance))

        # 5. 按距离排序并返回前k个结果
        candidates.sort(key=lambda x: x[1])
        return candidates[:k]

    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        if not self.is_trained:
            return {"status": "未训练"}

        total_vectors = sum(len(lst) for lst in self.inverted_lists.values())
        cluster_sizes = [len(self.inverted_lists[i]) for i in range(self.nlist)]

        # 计算压缩统计
        original_size_per_vector = self.dimension * 4  # 32位浮点数
        compressed_size_per_vector = self.m * (self.nbits / 8)
        compression_ratio = original_size_per_vector / compressed_size_per_vector

        return {
            "status": "已训练",
            "聚类数量": self.nlist,
            "向量总数": total_vectors,
            "向量维度": self.dimension,
            "搜索聚类数": self.nprobe,
            "子空间数量": self.m,
            "量化位数": self.nbits,
            "每子空间质心数": 2 ** self.nbits,
            "压缩比": f"{compression_ratio:.2f}x",
            "原始向量大小": f"{original_size_per_vector} bytes",
            "压缩向量大小": f"{compressed_size_per_vector} bytes",
            "各聚类大小": cluster_sizes,
            "平均聚类大小": np.mean(cluster_sizes),
            "聚类大小标准差": np.std(cluster_sizes)
        }


async def main():
    """主函数：演示IVF_PQ索引的使用"""

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
    print("IVF_PQ 倒排文件与乘积量化索引算法演示")
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

    # 确保向量维度能被子空间数量整除
    dimension = vectors.shape[1]
    m = 4  # 子空间数量
    if dimension % m != 0:
        # 如果不能整除，调整子空间数量
        for new_m in [2, 8, 16, 32]:
            if dimension % new_m == 0:
                m = new_m
                break
        else:
            # 如果还是不能整除，填充向量
            pad_size = m - (dimension % m)
            vectors = np.pad(vectors, ((0, 0), (0, pad_size)), mode='constant')
            print(f"向量维度填充到: {vectors.shape[1]}")

    # 创建IVF_PQ索引
    # 使用3个聚类，1个探测聚类，4个子空间，3位量化（8个质心，适合小数据集）
    index = IVF_PQ_Index(nlist=3, nprobe=1, m=m, nbits=3)

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

    # 测试乘积量化的编码和解码
    print("\n" + "=" * 40)
    print("乘积量化测试")
    print("=" * 40)
    
    # 选择第一个向量进行测试
    test_vector = vectors[0]
    print(f"原始向量前10维: {test_vector[:10]}")
    
    # 编码
    pq_code = index.pq.encode(test_vector.reshape(1, -1))
    print(f"PQ编码: {pq_code[0]}")
    
    # 解码
    decoded_vector = index.pq.decode(pq_code)
    print(f"解码向量前10维: {decoded_vector[0][:10]}")
    
    # 计算重构误差
    reconstruction_error = np.linalg.norm(test_vector - decoded_vector[0])
    print(f"重构误差: {reconstruction_error:.4f}")

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
        
        # 如果原始向量被填充，查询向量也需要填充
        if query_vector.shape[0] != vectors.shape[1]:
            pad_size = vectors.shape[1] - query_vector.shape[0]
            query_vector = np.pad(query_vector, (0, pad_size), mode='constant')
        
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
            print(f"     估算距离: {distance:.4f}, 相似度: {similarity:.4f}")
            print(f"     描述: {candidate['description']}")
            print()

    # 性能对比：IVF_PQ vs IVF_FLAT vs 暴力搜索
    print("\n" + "=" * 60)
    print("性能和准确率对比")
    print("=" * 60)

    query = "我希望找一个温柔体贴的软件工程师"
    query_embeddings = await client.get_embeddings([query])
    query_vector = np.array(query_embeddings[0])
    
    # 如果原始向量被填充，查询向量也需要填充
    if query_vector.shape[0] != vectors.shape[1]:
        pad_size = vectors.shape[1] - query_vector.shape[0]
        query_vector = np.pad(query_vector, (0, pad_size), mode='constant')

    # IVF_PQ搜索
    start_time = time.time()
    ivf_pq_results = index.search(query_vector, k=3)
    ivf_pq_time = time.time() - start_time

    # 暴力搜索（作为基准）
    start_time = time.time()
    distances = []
    for i, vector in enumerate(vectors):
        distance = np.linalg.norm(vector - query_vector)
        distances.append((candidate_ids[i], distance))
    distances.sort(key=lambda x: x[1])
    brute_results = distances[:3]
    brute_time = time.time() - start_time

    print(f"IVF_PQ搜索耗时: {ivf_pq_time:.6f}秒")
    print(f"暴力搜索耗时: {brute_time:.6f}秒")
    print(f"速度提升: {brute_time / ivf_pq_time:.2f}x")

    print("\nIVF_PQ搜索结果:")
    for rank, (vector_id, distance) in enumerate(ivf_pq_results, 1):
        candidate = next(c for c in candidates if c["id"] == vector_id)
        print(f"  {rank}. {candidate['name']} (估算距离: {distance:.4f})")

    print("\n暴力搜索结果（精确）:")
    for rank, (vector_id, distance) in enumerate(brute_results, 1):
        candidate = next(c for c in candidates if c["id"] == vector_id)
        print(f"  {rank}. {candidate['name']} (精确距离: {distance:.4f})")

    # 验证结果一致性
    ivf_pq_ids = [r[0] for r in ivf_pq_results]
    brute_ids = [r[0] for r in brute_results]
    accuracy = len(set(ivf_pq_ids) & set(brute_ids)) / len(brute_ids)
    print(f"\n结果准确率: {accuracy:.2%}")
    
    # 计算距离估算误差
    common_ids = set(ivf_pq_ids) & set(brute_ids)
    if common_ids:
        errors = []
        for vid in common_ids:
            ivf_pq_dist = next(d for v, d in ivf_pq_results if v == vid)
            brute_dist = next(d for v, d in brute_results if v == vid)
            error = abs(ivf_pq_dist - brute_dist) / brute_dist
            errors.append(error)
        avg_error = np.mean(errors)
        print(f"平均距离估算误差: {avg_error:.2%}")

    print("\n" + "=" * 60)
    print("IVF_PQ算法优势总结")
    print("=" * 60)
    print("1. 存储压缩：通过乘积量化大幅减少内存使用")
    print("2. 快速搜索：倒排文件索引减少搜索空间")
    print("3. 近似准确：在压缩的同时保持较高的搜索准确率")
    print("4. 可扩展性：适合大规模向量数据库应用")
    print("=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
