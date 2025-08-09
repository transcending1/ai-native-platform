# Bot细节需求描述

## 项目路径

1. APP路径:api/backend_management/bot
2. APP下面的子模块名称: bot
3. 用户APP模型的路径：/api/backend_management/user/models/user.py 你可以参考用户模型进行外键建模
4. Web端APP子项目: new_web/src/views/Bot Bot组件: new_web/src/views/Bot/components/*
5. Web端左侧菜单栏（Sidebar）：new_web/src/components/Sidebar.vue
6. API文档路径： api_schema.yaml （你去看一下就知道Web端应该如何对接服务端）


## 核心代码目录结构
api/backend_management/
├── bot/
│   ├── models/
│   │   └── bot.py                          # ✅ Bot模型和协作者模型
│   ├── serializers/
│   │   └── bot.py                          # ✅ Bot序列化器，支持Base64图片上传
│   ├── views/
│   │   └── bot.py                          # ✅ Bot视图集，深度集成LangGraph SDK
│   ├── tests/
│   │   └── test_bot.py                     # ✅ 完整测试用例，包含LangGraph模拟
│   └── urls.py                             # ✅ Bot URL路由配置
├── llm_api/
│   ├── urls.py                             # 🔧 添加bot路由
│   └── settings/
│       └── base.py                         # 🔧 添加bot到INSTALLED_APPS

new_web/src/
├── components/
│   └── Sidebar.vue                         # 🔧 添加Assistants管理菜单
├── router/
│   └── index.js                           # 🔧 添加Bot管理路由
├── api.js                                 # 🔧 添加Bot相关API方法
└── views/Bot/
    ├── Main.vue                           # ✅ Bot主页面，参考KnowledgeNamespace设计
    └── components/
        ├── CreateBotDialog.vue            # ✅ 创建Bot对话框
        └── BotSettingsDialog.vue          # ✅ Bot设置对话框，包含权限管理



## 第一版需求
1. 从Bot管理界面点击Bot头像可以进入Bot的调试，详情编辑界面
2. 详情页面细节设计，整体页面需要是响应式布局。界面总共分成三块：
    1.左侧：填写Prompt：人设与回复逻辑   
    2.中侧（编排栏）：Assistant各种配置文件的配置地方，每一栏都是可以折叠的，点击折叠栏会弹出具体配置  
    3.右侧（预览与调试对话框）：Assistant调试的对话框，点击保存按钮后 Assistant 的配置文件会得到更新。然后就可以在右侧的对话框中和 Assistant 进行对话交流。测试Bot的能力
3. Assistant配置---模型配置细节设计模型的选择从里面的list api去获取：api/backend_management/provider/views/provider.py （这里面包含了列出provider的核心逻辑）
有两种类型的模型，两个折叠框即可：
    1.问答模型
        "last_model": "Qwen3-30B-A3B-FP8",    # 非用户填写（从用户选择的模型中获取）
        "last_model_provider": "openai",   # 非用户填写（从用户选择的模型中获取）
        "last_temperature": 0,   # 用户填写（温度）
        "last_max_tokens": 5120,   # 用户填写（最大Token数量）
        "last_base_url": os.getenv('CHAT_MODEL_DEFAULT_BASE_URL'),   # 非用户填写（从用户选择的模型中获取）
        "last_api_key": os.getenv('CHAT_MODEL_DEFAULT_API_KEY'),  # 非用户填写（从用户选择的模型中获取）
        "last_extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": False    # 非用户填写（这个参数不需要提供给用户选择，直接为False即可）
            }
        }
    2.知识精排模型
        "knowledge_rerank_model": "Qwen3-30B-A3B-FP8",   # 非用户填写（从用户选择的模型中获取）
        "knowledge_rerank_model_provider": "openai",    # 非用户填写（从用户选择的模型中获取）
        "knowledge_rerank_temperature": 0,	    # 用户填写（温度）
        "knowledge_rerank_max_tokens": 5120,    # 用户填写（最大Token数量）
        "knowledge_rerank_base_url": os.getenv('CHAT_MODEL_DEFAULT_BASE_URL'),   # 非用户填写（从用户选择的模型中获取）
        "knowledge_rerank_api_key": os.getenv('CHAT_MODEL_DEFAULT_API_KEY'),   # 非用户填写（从用户选择的模型中获取）
        "knowledge_rerank_extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": False   # 非用户填写（这个参数不需要提供给用户选择，直接为False即可）
            }
        }
    模型配置层面用户可以填写的两个参数：
    1.temperature：浮点数 0-1
    2.max_tokens：最大Token数 0-正无穷

4. Assistant配置---记忆配置细节设计
    "memory_config": {
        "max_tokens": 2560,  # 用户填写（多轮对话记忆中最大的token数量）
    }

5. Assistant配置---普通知识RAG配置
    "rag_config": {
        "is_rag": True,    # （用户填写）是否开启普通知识的RAG模式，默认True
        "retrieve_top_n": 5,  #（用户填写）召回文档数量，3-100 默认：5
        "retrieve_threshold": 0.2,  #（用户填写）召回文档阈值 0-1 默认：0.2
        "is_rerank": True, # （用户填写）是否开启重排模式  默认：True
        "rerank_top_n": 3, # （用户填写）重排数量  3-100 默认：3  
        "rerank_threshold": 0.4, # （用户填写）重排文档阈值 0-1  默认 0.4
        "is_llm_rerank": True,    # （用户填写）是否进行大模型重排操作 默认 False
        "namespace_list": ["namespace1"],    # （用户选择知识命名空间，此处传入namespace的id）用户选择的知识库  默认为空  下拉框为自己创建的namespace和邀请协作进入的namespace名称。
        "is_structured_output": True # （非用户填写）默认为False
    }
    注：api/backend_management/knowledge/views/namespace.py  这里面可以获取namespace的列表，然后列出名字供用户选择
6. Assistant配置---工具知识RAG配置
    "tool_config": {
        "is_rag": True,    # （用户填写）是否开启工具知识的RAG模式，默认True
        "retrieve_top_n": 5,    #（用户填写）召回工具数量，3-100 默认：5
        "retrieve_threshold": 0.2,    #（用户填写）召回工具阈值 0-1 默认：0.2
        "is_rerank": True,  # （用户填写）是否开启重排模式  默认：True
        "rerank_top_n": 3,  # （用户填写）重排数量  3-100 默认：3  
        "rerank_threshold": 0.4,  # （用户填写）重排文档阈值 0-1  默认 0.4
        "is_llm_rerank": True,   # （用户填写）是否进行大模型重排操作 默认 False
        "max_iterations": 3, # （用户填写）Agent的最大迭代次数
        "namespace_list": ["namespace1"],   # （用户选择知识命名空间，此处传入namespace的id）用户选择的知识库  默认为空  下拉框为自己创建的namespace和邀请协作进入的namespace名称。
    }
7. Assistant配置---系统配置
    "sys_config": {
        "owner": "user1",  # （非用户填写）租户id，默认为当前用户id
    }


点击右上方的保存按钮就要把上面这么多的信息都更新到 Assistant 的配置里面
api/backend_management/core/extensions/tests/integration_tests/test_langgraph_sdk.py  里面下面这一个接口就是更新Bot的配置。根据用户传入的config。只需要更新config即可。
        langgraph_client.assistants.update(
            assistant_id=openai_assistant_id,   # 当前创建Bot的id
            config=config,  # 上面的配置文件组合起来的内容
        )
8. 右侧（预览与调试对话框）：Assistant调试的对话框 默认画一个即可，没必要立刻生效，还在调试Bot的对话框。默认画一个与Bot对话的窗口即可。


## 最新版需求
1. 右侧（预览与调试对话框）：Assistant调试的对话框需要支持和Bot的对话了。Stream展示Bot对话的内容。（说明：右侧调试就是简单的用户输入文字，点击发送按钮，Bot就会返回对话内容。Bot的对话内容需要支持Stream输出。）
2. 用户输入问题后服务端处理逻辑：
a. 先创建一个线程Thread:
```python
from langgraph_sdk import get_sync_client
from core.extensions.ext_langgraph import GRAPH_ID, langgraph_client
openai_assistant_id = 'cd398240-8244-4762-98d4-6d43bfdb3df7' # Bot的id.这是个测试用例。
thread = langgraph_client.threads.create(
    metadata={
        "assistant_id": openai_assistant_id,
    },
    graph_id=GRAPH_ID
)
# 第一轮对话:发送消息到Assistants
for stream_mode, chuck in langgraph_client.runs.stream(
        thread_id=thread['thread_id'],
        assistant_id=openai_assistant_id,
        input={"question": "我的名字叫小明"},
        stream_mode=["messages"]
):
    if stream_mode == "messages/partial":
        print(chuck[0]['content'])
# 第二轮对话:发送消息到Assistants,证明有记忆力
for stream_mode, chuck in langgraph_client.runs.stream(
        thread_id=thread['thread_id'],
        assistant_id=openai_assistant_id,
        input={"question": "我的名字是啥？"},
        stream_mode=["messages"]
):
    if stream_mode == "messages/partial":
        print(chuck[0]['content'])
# 第三轮对话:发送消息到Assistants,证明有RAG能力
for stream_mode, chuck in langgraph_client.runs.stream(
        thread_id=thread['thread_id'],
        assistant_id=openai_assistant_id,
        input={"question": "爱因斯坦会议室号码是多少？"},
        stream_mode=["messages"]
):
    if stream_mode == "messages/partial":
        print(chuck[0]['content'])
# 第四轮对话:发送消息到Assistants,证明有工具使用能力
for stream_mode, chuck in langgraph_client.runs.stream(
        thread_id=thread['thread_id'],
        assistant_id=openai_assistant_id,
        input={"question": "北京天气是多少？"},
        stream_mode=["messages"]
):
    if stream_mode == "messages/partial":
        print(chuck[0]['content'])
```
