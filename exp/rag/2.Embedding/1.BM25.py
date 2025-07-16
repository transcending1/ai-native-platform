#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM25算法教学案例 - 恋爱文档检索系统
========================================

这是一个生动形象的BM25算法教学案例，通过恋爱相关的文档来演示
在RAG（检索增强生成）场景中如何使用BM25进行文档检索。

BM25（Best Matching 25）是一种经典的信息检索算法，
广泛应用于搜索引擎和文档检索系统中。
"""

import math
import re
from collections import Counter
from typing import List, Dict, Tuple

import jieba  # 中文分词库


class BM25TeachingDemo:
    """
    BM25算法教学演示类
    
    这个类将通过恋爱文档检索的例子，生动地展示BM25算法的工作原理
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化BM25参数
        
        Args:
            k1: 控制词频饱和度的参数，通常取值1.2-2.0
            b: 控制文档长度归一化的参数，通常取值0.75
        """
        self.k1 = k1
        self.b = b
        self.documents = []  # 存储原始文档
        self.tokenized_docs = []  # 存储分词后的文档
        self.doc_freqs = []  # 存储每个文档的词频
        self.idf_values = {}  # 存储每个词的IDF值
        self.avg_doc_length = 0  # 平均文档长度

        print("🌹 欢迎来到BM25恋爱文档检索系统！ 🌹")
        print("我们将通过恋爱相关的文档来学习BM25算法~")

    def prepare_love_documents(self):
        """
        准备恋爱相关的示例文档
        这些文档将作为我们的知识库
        """
        self.documents = [
            {
                "id": 1,
                "title": "初次约会攻略",
                "content": "初次约会是恋爱关系中非常重要的一步。选择合适的地点很关键，可以选择咖啡厅、电影院或者公园。要注意穿着得体，保持良好的谈话氛围。记住要准时到达，展现你的诚意和尊重。"
            },
            {
                "id": 2,
                "title": "如何表白成功",
                "content": "表白是恋爱中的关键时刻。首先要选择合适的时机和地点，确保对方心情愉快。表白时要真诚，说出自己的真实感受。不要给对方太大压力，要给她思考的时间。记住，真诚是最重要的。"
            },
            {
                "id": 3,
                "title": "恋爱中的沟通技巧",
                "content": "良好的沟通是恋爱关系的基础。要学会倾听对方的想法和感受，不要急于反驳。表达自己观点时要温和而坚定。遇到分歧时，要保持冷静，寻找共同点。记住沟通是双向的，要给对方表达的机会。"
            },
            {
                "id": 4,
                "title": "维持长久关系的秘诀",
                "content": "长久的恋爱关系需要双方的努力和维护。要保持新鲜感，经常创造惊喜和浪漫。学会包容对方的缺点，同时也要成长自己。建立共同的目标和兴趣爱好。最重要的是要信任对方，给彼此足够的空间。"
            },
            {
                "id": 5,
                "title": "分手后的心理调适",
                "content": "分手是恋爱中痛苦但有时不可避免的经历。要接受自己的情绪，允许自己悲伤一段时间。不要急于开始新的恋情，先好好照顾自己。可以通过运动、旅行或学习新技能来转移注意力。记住每一次经历都是成长的机会。"
            }
        ]

        print(f"\n📚 已准备{len(self.documents)}篇恋爱相关文档：")
        for doc in self.documents:
            print(f"  📄 {doc['title']}")

    def tokenize_text(self, text: str) -> List[str]:
        """
        中文文本分词
        
        Args:
            text: 输入的中文文本
            
        Returns:
            分词后的词语列表
        """
        # 使用jieba进行中文分词
        words = jieba.cut(text, cut_all=False)

        # 过滤掉标点符号和空格，只保留有意义的词
        filtered_words = []
        for word in words:
            word = word.strip()
            if len(word) > 1 and not re.match(r'^[^\w]+$', word):
                filtered_words.append(word.lower())

        return filtered_words

    def build_index(self):
        """
        构建BM25索引
        这一步会对所有文档进行分词，并计算必要的统计信息
        """
        print("\n🔧 开始构建BM25索引...")

        # 1. 对所有文档进行分词
        for doc in self.documents:
            full_text = doc['title'] + ' ' + doc['content']
            tokens = self.tokenize_text(full_text)
            self.tokenized_docs.append(tokens)

            # 计算词频
            word_freq = Counter(tokens)
            self.doc_freqs.append(word_freq)

        # 2. 计算平均文档长度
        total_length = sum(len(doc) for doc in self.tokenized_docs)
        self.avg_doc_length = total_length / len(self.tokenized_docs)

        # 3. 计算IDF值（逆文档频率）
        all_words = set()
        for tokens in self.tokenized_docs:
            all_words.update(tokens)

        for word in all_words:
            # 计算包含该词的文档数量
            doc_count = sum(1 for doc_freq in self.doc_freqs if word in doc_freq)

            # 计算IDF：log((N - df + 0.5) / (df + 0.5))
            # N是总文档数，df是包含该词的文档数
            N = len(self.documents)
            idf = math.log((N - doc_count + 0.5) / (doc_count + 0.5))
            self.idf_values[word] = idf

        print(f"✅ 索引构建完成！")
        print(f"   📊 总文档数: {len(self.documents)}")
        print(f"   📊 平均文档长度: {self.avg_doc_length:.2f} 词")
        print(f"   📊 词汇表大小: {len(self.idf_values)} 个词")

    def calculate_bm25_score(self, query_tokens: List[str], doc_index: int) -> float:
        """
        计算查询与特定文档的BM25得分
        
        Args:
            query_tokens: 查询的分词结果
            doc_index: 文档索引
            
        Returns:
            BM25得分
        """
        score = 0.0
        doc_freq = self.doc_freqs[doc_index]
        doc_length = len(self.tokenized_docs[doc_index])

        for word in query_tokens:
            if word in doc_freq:
                # 获取词频和IDF
                tf = doc_freq[word]  # 词频
                idf = self.idf_values.get(word, 0)  # IDF值

                # BM25公式的核心计算
                # score += IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_length / avg_doc_length)))
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))

                word_score = idf * (numerator / denominator)
                score += word_score

                # 详细展示计算过程（用于教学）
                print(f"    🔍 词语 '{word}': tf={tf}, idf={idf:.3f}, 贡献得分={word_score:.3f}")

        return score

    def search(self, query: str, top_k: int = 3) -> List[Tuple[Dict, float]]:
        """
        使用BM25算法搜索相关文档
        
        Args:
            query: 用户查询
            top_k: 返回前k个最相关的文档
            
        Returns:
            排序后的文档和得分列表
        """
        print(f"\n🔍 用户查询: '{query}'")
        print("=" * 50)

        # 对查询进行分词
        query_tokens = self.tokenize_text(query)
        print(f"📝 查询分词结果: {query_tokens}")

        # 计算每个文档的BM25得分
        results = []
        for i, doc in enumerate(self.documents):
            print(f"\n📄 计算文档 '{doc['title']}' 的相关度:")
            score = self.calculate_bm25_score(query_tokens, i)
            results.append((doc, score))
            print(f"   🎯 总得分: {score:.3f}")

        # 按得分排序
        results.sort(key=lambda x: x[1], reverse=True)

        print(f"\n🏆 检索结果 (Top {top_k}):")
        print("=" * 50)

        top_results = results[:top_k]
        for i, (doc, score) in enumerate(top_results, 1):
            print(f"{i}. 📚 {doc['title']}")
            print(f"   🎯 相关度得分: {score:.3f}")
            print(f"   📖 内容预览: {doc['content'][:50]}...")
            print()

        return top_results

    def explain_bm25_formula(self):
        """
        详细解释BM25公式的含义
        """
        print("\n📖 BM25公式详解:")
        print("=" * 50)
        print("BM25(q,d) = Σ IDF(w) * (tf(w,d) * (k1 + 1)) / (tf(w,d) + k1 * (1 - b + b * |d|/avgdl))")
        print()
        print("🔤 符号说明:")
        print("  • q: 查询 (query)")
        print("  • d: 文档 (document)")
        print("  • w: 查询中的词语 (word)")
        print("  • tf(w,d): 词语w在文档d中的频率")
        print("  • IDF(w): 词语w的逆文档频率")
        print("  • |d|: 文档d的长度")
        print("  • avgdl: 平均文档长度")
        print("  • k1, b: 调节参数")
        print()
        print("🎯 参数作用:")
        print(f"  • k1 = {self.k1}: 控制词频饱和度，避免高频词过度影响")
        print(f"  • b = {self.b}: 控制文档长度归一化，平衡长短文档")
        print()
        print("💡 算法思想:")
        print("  1. 词频越高，相关度越高（但有饱和点）")
        print("  2. 包含该词的文档越少，该词越重要（IDF）")
        print("  3. 考虑文档长度，避免长文档占优势")


def demonstrate_bm25_love_search():
    """
    演示BM25恋爱文档检索系统
    """
    print("🌹💕 BM25恋爱文档检索系统演示 💕🌹")
    print("=" * 60)

    # 创建BM25检索系统
    bm25_demo = BM25TeachingDemo()

    # 准备文档并构建索引
    bm25_demo.prepare_love_documents()
    bm25_demo.build_index()

    # 解释BM25公式
    bm25_demo.explain_bm25_formula()

    # 演示不同的查询场景
    test_queries = [
        "如何进行第一次约会",
        "表白的技巧和方法",
        "恋爱中怎么沟通",
        "分手了很难过怎么办"
    ]

    for query in test_queries:
        bm25_demo.search(query, top_k=3)
        input("\n按回车键继续下一个查询演示...")

    print("\n🎓 教学总结:")
    print("=" * 50)
    print("1. BM25是经典的信息检索算法，在RAG系统中广泛应用")
    print("2. 通过词频、逆文档频率和文档长度归一化来计算相关度")
    print("3. 相比简单的词频匹配，BM25能更好地处理长文档和常见词")
    print("4. 在实际RAG应用中，通常与向量检索结合使用，提高召回效果")


if __name__ == "__main__":
    # 运行演示
    demonstrate_bm25_love_search()
