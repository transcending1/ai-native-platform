from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

documents = TextLoader("./白富美.txt").load()
text_splitter = CharacterTextSplitter(
    chunk_size=300,  # 每个文本块的大小为300个字符
    chunk_overlap=100,  # 每个文本块之间的重叠部分为100个字符
)
chunks = text_splitter.split_documents(documents)
for i, chunk in enumerate(chunks, 1):
    print(f"\n--- 第 {i} 个文档块 ---")
    print(f"内容: {chunk.page_content}")
    print(f"元数据: {chunk.metadata}")
    print("-" * 50)
