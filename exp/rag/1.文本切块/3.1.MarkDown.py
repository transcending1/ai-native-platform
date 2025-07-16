from pprint import pprint

from langchain_text_splitters import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "H1"),
    ("##", "H2"),
    ("###", "H3"),
    ("####", "H4"),
    ("#####", "H5"),
    ("######", "H6"),
]

# MD splits
markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False
)

new_markdown_document = '''
# 会议室号码 \n\n    
## xxx会议室号码是多少？ \n\n 123456789 \n\n'''

res = markdown_splitter.split_text(new_markdown_document)

pprint(res)
