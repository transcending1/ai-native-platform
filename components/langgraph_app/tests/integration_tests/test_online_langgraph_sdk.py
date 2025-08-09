import allure

from core.extensions.ext_langgraph import GRAPH_ID, get_sync_client


def test_assistants():
    langgraph_client = get_sync_client(url="http://222.186.32.152:32710", api_key=None)
    openai_assistant_id = 'cd398240-8244-4762-98d4-6d43bfdb3df7'

    with allure.step("进入调试界面创建测试Thread"):
        thread = langgraph_client.threads.create(
            metadata={
                "assistant_id": openai_assistant_id,
            },
            graph_id=GRAPH_ID
        )

    with allure.step("第一轮对话:发送消息到Assistants"):
        for stream_mode, chuck in langgraph_client.runs.stream(
                thread_id=thread['thread_id'],
                assistant_id=openai_assistant_id,
                input={"question": "我的名字叫小明"},
                stream_mode=["messages"]
        ):
            if stream_mode == "messages/partial":
                print(chuck[0]['content'])

    with allure.step("第二轮对话:发送消息到Assistants,证明有记忆力"):
        for stream_mode, chuck in langgraph_client.runs.stream(
                thread_id=thread['thread_id'],
                assistant_id=openai_assistant_id,
                input={"question": "我的名字是啥？"},
                stream_mode=["messages"]
        ):
            if stream_mode == "messages/partial":
                print(chuck[0]['content'])

    with allure.step("第三轮对话:发送消息到Assistants,证明有RAG能力"):
        for stream_mode, chuck in langgraph_client.runs.stream(
                thread_id=thread['thread_id'],
                assistant_id=openai_assistant_id,
                input={"question": "爱因斯坦会议室号码是多少？"},
                stream_mode=["messages"]
        ):
            if stream_mode == "messages/partial":
                print(chuck[0]['content'])

    with allure.step("第四轮对话:发送消息到Assistants,证明有工具使用能力"):
        for stream_mode, chuck in langgraph_client.runs.stream(
                thread_id=thread['thread_id'],
                assistant_id=openai_assistant_id,
                input={"question": "北京天气是多少？"},
                stream_mode=["messages"]
        ):
            if stream_mode == "messages/partial":
                print(chuck[0]['content'])

    # with allure.step("下次点击调试的时候或者用户点击情况的时候重新创建测试thread"):
    #     all_threads = langgraph_client.threads.search(
    #         metadata={
    #             "assistant_id": openai_assistant_id,
    #         },
    #         limit=10,
    #         offset=0
    #     )
    #     for _thread in all_threads:
    #         langgraph_client.threads.delete(
    #             thread_id=_thread['thread_id']
    #         )
