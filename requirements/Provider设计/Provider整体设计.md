# Provider管理系统---Provider管理

## 项目路径

1. APP路径:api/backend_management/provider
2. APP下面的子模块名称: provider
3. 用户APP模型的路径：/api/backend_management/user/models/user.py 你可以参考用户模型进行外键建模
4. API文档路径：api_schema.yaml（你去看一下就知道怎么对接服务端）
5. Web端APP子项目: new_web/src/views/ProviderManagement  你可以在new_web/src/views/ProviderManagement/components 中创建组件   可以在new_web/src/views/ProviderManagement/Main.vue中创建组件编排逻辑


# 第一版需求
左侧菜单栏（new_web/src/components/Sidebar.vue）中的系统管理中加一项Provider管理。点击可以进入Provider管理界面。
进入界面后左侧菜单栏有多种选项，具体模型如下所示：
1.全局配置
2.Rerank模型
3.ASR模型
4.TTS模型
5.LLM模型
类似图片中的布局风格：
new_web/src/components/UserInfo.vue  这个风格

点击Provider管理界面中的每一项（
1.全局配置
2.Rerank模型
3.ASR模型
4.TTS模型
5.LLM模型
）可以在右侧菜单栏中显示对应的Provider列表。
可以通过名称进行搜索
new_web/src/views/KnowledgeNamespace/Main.vue  类似这个页面风格

全局配置的这个选项比较特殊，点击之后右侧菜单栏显示的内容不是 new_web/src/views/KnowledgeNamespace/Main.vue  这个页面风格

后端建模需求：目前先把上面5个概念都建立一个model  全局配置  Rerank模型  ASR模型  TTS模型   LLM模型 全都建立一个model 独立提供API。


# 第二版需求

1. 全局配置不需要配置model，存储到DB里面，而是直接使用Django内置的缓存存储（背后存储到了redis中）
2. 全局配置不需要进行添加的操作。而是基于固定的模式之上进行配置。
我现在需要有两个全局配置的需求：
1. 全局配置的LLM 编码模型。有一系列参数暴露出来可以供用户进行配置。
2. 全局配置的Embedding模型。有一系列参数暴露出来可以供用户配置。在 new_web/src/views/ProviderManagement/components/GlobalConfigPanel.vue 这个文件下面固定写死上面的LLM配置  和 Embedding 配置的两个选项即可，没必要新增。
3. 服务端也需要移除Global对于模型层的CRUD的操作。转向对Django内置redis的操作。

# 最新版需求
我需要通过用户提问的方式去生成全局Embedding模型的接入方式
A.代码的生成:根据用户的需求生成符合业务逻辑的接口适配器，代码调用方式如下

```python
import os
import django

from core.agent.coding.embedding import embedding_code_generator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm_api.settings.dev_settings")
django.setup()


def test_embedding_coding():
    user_demand = """
    headers = {
                "Content-Type": "application/json",
            }
    请求头：Authorization：Bearer xxxxxxxxxxxxxxxxxxxxxxx 用户的Token
    请求体：inputs 内嵌套文本  ['文本1','文本2']
    接口：http://222.186.32.152:10001/embed

    实现一波Embedding的请求示例
    Token为 aB3fG7kL9mN1pQ5rS8tU2vW4xYz0Aa
    """
    # 更具用户需求生成底代码
    is_success, code = embedding_code_generator.generation(user_demand, redis_key="global_embedding")
    # is_success 代表代码生成是否运行单元测试成功
    print(is_success)
    # code 代表单元测试用例代码
    print(code)
```

B.API的设计：注册上来的Embedding模型需要提供一个统一的API给外部调用,Embedding模型调用的方式如下：

```python
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
```

Web端交互需求如下：
Web端重点优化的地方：new_web/src/views/ProviderManagement/components/GlobalConfigPanel.vue
还需要对接服务端生成的API
equenceDiagram
    participant U as 用户
    participant S as 系统
    U->>S: 点击"集成Embedding模型"
    S->>U: 显示创建向导
    U->>S: 输入接口文档/个人需求描述，点击AI生成，（这个时候时间比较长，要提醒用户耐心等待。）
    S->>U: 显示AI解析结果和返回的代码
    U->>S: 调整生成参数
    S->>U: 返回可编辑代码（并且右边有一个测试按钮，可以点击一波返回测试结果看看生成的代码是否符合预期）
    U->>S: 确认保存，集成成功，并且可以再次根据自己的需求或者编辑代码去集成，增量提需求进行修改