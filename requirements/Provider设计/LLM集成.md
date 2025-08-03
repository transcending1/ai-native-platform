# Provider管理系统---LLM集成与管理

## 项目路径

1. APP路径:api/backend_management/provider
2. APP下面的子模块名称: provider
3. 用户APP模型的路径：/api/backend_management/user/models/user.py 你可以参考用户模型进行外键建模
4. API文档路径：api_schema.yaml（你去看一下就知道怎么对接服务端）
5. Web端APP子项目: new_web/src/views/ProviderManagement  大模型管理主界面：new_web/src/views/ProviderManagement/components/LLMModelPanel.vue

# 第一版需求
1.模型ID：模型厂商提供的唯一ID，用于区别模型
2.提供商：模型厂商的名称，下拉选项：
- ``openai``           
- ``anthropic``           
- ``azure_openai``        
- ``azure_ai``            
- ``google_vertexai``  
- ``google_genai``       
- ``bedrock``            
- ``bedrock_converse``    
- ``cohere``              
- ``fireworks``           
- ``together``           
- ``mistralai``          
- ``huggingface``      
- ``groq``              
- ``ollama``             
- ``google_anthropic_vertex``    
- ``deepseek``          
- ``ibm``               
- ``nvidia``             
- ``xai``                 
- ``perplexity``       
3.API密钥：模型认证key
4.API基础URL：模型的endpoint
5.是否启用：模型是否正式在平台中投入使用。
服务端也仅仅需要保留上面的几个字段即可（服务端已经实现了一波，继续迭代）。
- 并且服务端要使用django内置的缓存把上面的内容缓存起来。key 就是 model_{模型id}  让我后面可以通过模型id快速获取模型的基础参数即可  
- value 就是json序列化的object。（CRUD的时候保证缓存和数据库的一致性即可。）

Web端还需要有测试的功能，比如用户填写了上面5个关键的字段，Web端需要调用服务端测试的接口去测试到底大模型有没有生效。
服务端应该调用接口的方式如下：
```python
from core.models.llm import llm


@pytest.mark.asyncio
async def test_normal_llm():
    with allure.step("调用大语言模型调试"):
        # 调用大语言模型
        res = llm.invoke(
            "你是谁？",
            config={
                "configurable": {
                    "model": "Qwen3-30B-A3B-FP8", # 模型ID
                    "model_provider": "openai", # 模型提供商
                    "temperature": 0.1, # 固定写死
                    "base_url": os.getenv('CHAT_MODEL_DEFAULT_BASE_URL'), # 基础URL
                    "api_key": os.getenv('CHAT_MODEL_DEFAULT_API_KEY'), # API密钥
                }
            }
        )
        # res.content是一个字符串，大模型返回的内容
        print(res.content)
```