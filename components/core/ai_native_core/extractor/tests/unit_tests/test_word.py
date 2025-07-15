import os
from pprint import pprint

import pytest

from components.core.ai_native_core.extractor.word import DocxLoader, VisionPictureConfig


@pytest.mark.asyncio
async def test_word():
    word_loader = DocxLoader(
        file_path='files/test.docx',
        tenant_id="test_tenant",
        document_id="test_document_id",
        is_vision_picture_understanding=True,
        vision_model_config = VisionPictureConfig(
            model="doubao-1-5-vision-lite-250315",
            model_provider="openai",
            base_url="https://ark.cn-beijing.volces.com/api/v3/",
            api_key=os.getenv('DOUBAO_API_KEY'),  # Replace with your actual API key
            temperature=0,
            max_tokens=4096,
        )
    )
    res = word_loader.load()
    pprint(res)
    with open("files/test.md", "w", encoding="utf-8") as f:
        for item in res:
            f.write(item.page_content + "\n\n")
