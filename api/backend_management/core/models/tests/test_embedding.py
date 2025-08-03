from core.models.embedding import embedding


def test_global_embedding():
    texts = ["Deep Learning is not...", "Deep learning is..."]
    texts_response = embedding.embed_documents(texts)
    assert texts_response is not None
    print("Status:", "ok")
    print("Response:", texts_response)
    text_response = embedding.embed_query("What is Deep Learning?")
    # assert text_response is not None
    print("Status:", "ok")
    print("Response:", text_response)
