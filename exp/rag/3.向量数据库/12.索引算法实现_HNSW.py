import asyncio
import heapq
import math
import random
from typing import List, Dict, Tuple, Set, Optional

from tang_yuan_mlops_sdk.llm.embedding import EmbeddingClient

from settings import embedding_token


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """计算欧几里得距离"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


class HNSWNode:
    """HNSW图中的节点"""

    def __init__(self, node_id: int, vector: List[float], data: Optional[Dict] = None):
        self.id = node_id
        self.vector = vector
        self.data = data or {}
        # connections[layer] = set of connected node ids
        self.connections: Dict[int, Set[int]] = {}

    def add_connection(self, layer: int, neighbor_id: int):
        """在指定层添加连接"""
        if layer not in self.connections:
            self.connections[layer] = set()
        self.connections[layer].add(neighbor_id)

    def remove_connection(self, layer: int, neighbor_id: int):
        """在指定层移除连接"""
        if layer in self.connections:
            self.connections[layer].discard(neighbor_id)

    def get_connections(self, layer: int) -> Set[int]:
        """获取指定层的连接"""
        return self.connections.get(layer, set())


class HNSW:
    """分层可导航小世界图索引"""

    def __init__(self, M: int = 16, ef_construction: int = 200, ml: float = 1 / math.log(2)):
        """
        初始化HNSW参数
        
        Args:
            M: 每个节点在每层的最大连接数
            ef_construction: 构建时的候选集大小
            ml: 层级因子，用于确定节点的最大层级
        """
        self.M = M
        self.max_M = M  # 0层的最大连接数
        self.max_M0 = M * 2  # 其他层的最大连接数
        self.ef_construction = ef_construction
        self.ml = ml

        self.nodes: Dict[int, HNSWNode] = {}
        self.entry_point: Optional[int] = None
        self.layer_count = 0

    def _get_random_level(self) -> int:
        """随机生成节点层级"""
        level = 0
        while random.random() < 0.5 and level < 16:
            level += 1
        return level

    def _search_layer(self, query: List[float], entry_points: List[int],
                      num_closest: int, layer: int) -> List[Tuple[float, int]]:
        """在指定层搜索最近邻"""
        visited = set()
        candidates = []
        w = []  # 动态列表

        # 初始化候选集
        for ep in entry_points:
            if ep in self.nodes:
                dist = euclidean_distance(query, self.nodes[ep].vector)
                heapq.heappush(candidates, (-dist, ep))  # 最大堆
                heapq.heappush(w, (dist, ep))  # 最小堆
                visited.add(ep)

        while candidates:
            current_dist, current = heapq.heappop(candidates)
            current_dist = -current_dist

            # 如果当前距离比w中最远的距离还大，停止搜索
            if w and current_dist > w[0][0]:
                break

            # 检查当前节点的邻居
            neighbors = self.nodes[current].get_connections(layer)
            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    dist = euclidean_distance(query, self.nodes[neighbor_id].vector)

                    if len(w) < num_closest:
                        heapq.heappush(candidates, (-dist, neighbor_id))
                        heapq.heappush(w, (dist, neighbor_id))
                    elif dist < w[0][0]:
                        heapq.heappush(candidates, (-dist, neighbor_id))
                        heapq.heapreplace(w, (dist, neighbor_id))

        return w

    def _select_neighbors_heuristic(self, candidates: List[Tuple[float, int]],
                                    M: int) -> List[int]:
        """启发式选择邻居"""
        if len(candidates) <= M:
            return [node_id for _, node_id in candidates]

        # 简单策略：选择距离最近的M个邻居
        candidates.sort(key=lambda x: x[0])
        return [node_id for _, node_id in candidates[:M]]

    def insert(self, node_id: int, vector: List[float], data: Optional[Dict] = None):
        """插入新节点"""
        level = self._get_random_level()
        new_node = HNSWNode(node_id, vector, data)
        self.nodes[node_id] = new_node

        # 如果是第一个节点，设为入口点
        if self.entry_point is None:
            self.entry_point = node_id
            self.layer_count = level + 1
            return

        entry_points = [self.entry_point]

        # 从顶层搜索到level+1层
        for lc in range(self.layer_count - 1, level, -1):
            entry_points = [ep for _, ep in self._search_layer(vector, entry_points, 1, lc)]

        # 从level层到0层
        for lc in range(min(level, self.layer_count - 1), -1, -1):
            candidates = self._search_layer(vector, entry_points, self.ef_construction, lc)

            # 选择邻居
            if lc == 0:
                neighbors = self._select_neighbors_heuristic(candidates, self.max_M0)
            else:
                neighbors = self._select_neighbors_heuristic(candidates, self.max_M)

            # 建立双向连接
            for neighbor_id in neighbors:
                new_node.add_connection(lc, neighbor_id)
                self.nodes[neighbor_id].add_connection(lc, node_id)

                # 检查邻居是否超过最大连接数，如果是则修剪
                neighbor_connections = self.nodes[neighbor_id].get_connections(lc)
                if lc == 0 and len(neighbor_connections) > self.max_M0:
                    self._prune_connections(neighbor_id, lc, self.max_M0)
                elif lc > 0 and len(neighbor_connections) > self.max_M:
                    self._prune_connections(neighbor_id, lc, self.max_M)

            entry_points = neighbors

        # 更新入口点
        if level > self.layer_count - 1:
            self.entry_point = node_id
            self.layer_count = level + 1

    def _prune_connections(self, node_id: int, layer: int, max_connections: int):
        """修剪节点的连接"""
        node = self.nodes[node_id]
        connections = list(node.get_connections(layer))

        if len(connections) <= max_connections:
            return

        # 计算到所有邻居的距离
        candidates = []
        for neighbor_id in connections:
            dist = euclidean_distance(node.vector, self.nodes[neighbor_id].vector)
            candidates.append((dist, neighbor_id))

        # 选择保留的邻居
        kept_neighbors = self._select_neighbors_heuristic(candidates, max_connections)

        # 移除多余的连接
        for neighbor_id in connections:
            if neighbor_id not in kept_neighbors:
                node.remove_connection(layer, neighbor_id)
                self.nodes[neighbor_id].remove_connection(layer, node_id)

    def search(self, query: List[float], k: int, ef: Optional[int] = None) -> List[Tuple[float, int, Dict]]:
        """搜索k个最近邻"""
        if ef is None:
            ef = max(self.ef_construction, k)

        if self.entry_point is None:
            return []

        entry_points = [self.entry_point]

        # 从顶层搜索到第1层
        for lc in range(self.layer_count - 1, 0, -1):
            entry_points = [ep for _, ep in self._search_layer(query, entry_points, 1, lc)]

        # 在第0层搜索
        candidates = self._search_layer(query, entry_points, ef, 0)

        # 返回前k个结果
        results = []
        candidates.sort(key=lambda x: x[0])
        for i, (dist, node_id) in enumerate(candidates[:k]):
            results.append((dist, node_id, self.nodes[node_id].data))

        return results


async def test_hnsw():
    """测试HNSW算法"""
    print("开始测试HNSW算法...")

    # 候选人数据
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

    # 初始化Embedding客户端
    client = EmbeddingClient(base_url="http://222.186.32.152:10001", token=embedding_token)

    # 获取所有候选人的embedding
    print("正在获取候选人embedding...")
    texts = [candidate["description"] for candidate in candidates]
    embeddings = await client.get_embeddings(texts)

    # 创建HNSW索引
    print("创建HNSW索引...")
    hnsw = HNSW(M=8, ef_construction=100)

    # 插入数据
    print("插入数据到HNSW索引...")
    for i, (candidate, embedding) in enumerate(zip(candidates, embeddings)):
        hnsw.insert(
            node_id=candidate["id"],
            vector=embedding,
            data={"name": candidate["name"], "description": candidate["description"]}
        )

    print(f"索引构建完成，共有 {len(hnsw.nodes)} 个节点，{hnsw.layer_count} 层")

    # 测试查询
    queries = [
        "寻找一个喜欢运动的女生",
        "找一个有艺术气质的伴侣",
        "希望找一个温柔体贴的女生",
        "寻找聪明有智慧的女性"
    ]

    print("\n开始测试查询...")
    for query in queries:
        print(f"\n查询: {query}")

        # 获取查询embedding
        query_embeddings = await client.get_embeddings([query])
        query_vector = query_embeddings[0]

        # 搜索最相似的3个候选人
        results = hnsw.search(query_vector, k=3, ef=50)

        print("搜索结果:")
        for i, (distance, node_id, data) in enumerate(results, 1):
            print(f"  {i}. {data['name']} (距离: {distance:.4f})")
            print(f"     {data['description']}")

    # 性能统计
    print(f"\n索引统计:")
    print(f"总节点数: {len(hnsw.nodes)}")
    print(f"层数: {hnsw.layer_count}")
    print(f"入口点: {hnsw.entry_point}")

    # 显示每层的节点分布
    layer_distribution = {}
    for node in hnsw.nodes.values():
        max_layer = max(node.connections.keys()) if node.connections else 0
        layer_distribution[max_layer] = layer_distribution.get(max_layer, 0) + 1

    print("层级分布:")
    for layer in sorted(layer_distribution.keys(), reverse=True):
        print(f"  第{layer}层: {layer_distribution[layer]} 个节点")


if __name__ == "__main__":
    asyncio.run(test_hnsw())
