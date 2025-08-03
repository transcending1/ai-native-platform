from typing import List
from django.core.cache import cache
from langchain_core.embeddings import Embeddings
import json


# 如果有额外的导包需求不能在这里导入:比如requests等,在函数里面导入即可。

class GlobalEmbedding(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs.
        返回内容示例：Response: [[0.5, 0.6, 0.7], [0.5, 0.6, 0.7], ...]
        """
        code_mapping = json.loads(cache.get("global_embedding"))
        _code = code_mapping.get('embed_documents')
        exec(_code)
        return locals()['embed_documents'](self, texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed query text.
        返回内容示例：Response: [-0.030950097, -0.042273305, -0.03612379, xxx]
        """
        # 如果要导包就在函数内部导包即可
        code_mapping = json.loads(cache.get("global_embedding"))
        _code = code_mapping.get('embed_query')
        exec(_code)
        return locals()['embed_query'](self, text)


embedding = GlobalEmbedding()


