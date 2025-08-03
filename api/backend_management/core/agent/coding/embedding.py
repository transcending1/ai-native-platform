from core.agent.coding.base import CodeGeneration

code_template = """from typing import List

from langchain_core.embeddings import Embeddings
# 如果有额外的导包需求不能在这里导入:比如requests等,在函数里面导入即可。

class GlobalEmbedding(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        \"""Embed search docs.
        返回内容示例：Response: [[0.5, 0.6, 0.7], [0.5, 0.6, 0.7], ...]
        \"""
        # 如果要导包就在函数内部导包即可
        return [[0.5, 0.6, 0.7] for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        \"""Embed query text.
        返回内容示例：Response: [-0.030950097, -0.042273305, -0.03612379, xxx]
        \"""
        # 如果要导包就在函数内部导包即可
        return self.embed_documents([text])[0]


embedding = GlobalEmbedding()

def test_case():
    texts = ["Deep Learning is not...", "Deep learning is..."]
    texts_response = embedding.embed_documents(texts)
    assert texts_response is not None
    print("Status:", "ok")
    print("Response:", texts_response)
    text_response = embedding.embed_query("What is Deep Learning?")
    # assert text_response is not None
    print("Status:", "ok")
    print("Response:", text_response)
"""

system_prompt_patch = """
1.在这个案例中，单元测试用例直接使用代码模版里面的测试用例即可，没必要再去自己生成了。
2.你只需要根据用户需求生成代码模版中的代码即可。你只需要在embed_documents，embed_query方法中实现对应的逻辑。其余内容不要去变更。不要加入__init__等方法。
3.如果需要导包就在函数内部进行导包，而不是在最外侧去导包。因为我后续要通过反射的机制把里面的代码抽离出来存储在一个单独的地方，所以逻辑和环境的完整性需要保证，所以导包的信息要放在函数中。
4.这是一个Embedding模型接入的场景，对接Embedding模型的方式的详细信息，你只需要帮忙实现对接的代码逻辑即可。
"""

embedding_code_generator = CodeGeneration(
    code_template=code_template,
    system_prompt_patch=system_prompt_patch,
    to_extract_class_name="GlobalEmbedding",
    to_extract_function_list=["embed_documents", "embed_query"]
)
