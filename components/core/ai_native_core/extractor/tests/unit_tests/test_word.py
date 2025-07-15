from pprint import pprint

import pytest

from components.core.ai_native_core.extractor.word import DocxLoader


@pytest.mark.asyncio
async def test_word():
    word_loader = DocxLoader(file_path='files/test.docx')
    res = word_loader.load()
    pprint(res)
    with open("files/test.md", "w", encoding="utf-8") as f:
        for item in res:
            f.write(item.page_content + "\n\n")
            f.write(str(item.metadata) + "\n\n")
