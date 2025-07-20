from langchain_core.messages import AIMessage, RemoveMessage, trim_messages
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END
from langgraph.graph import START, StateGraph

from agent.configuration import Configuration
from agent.rag import get_rag_knowledge_context, rag_prompt_template, RAGAnswer, common_knowledge_retrieve, \
    common_knowledge_rerank, common_knowledge_llm_rerank
from agent.state import State, OutputState, InputState
from agent.tool import tool_knowledge_retrieve, tool_knowledge_rerank, tool_knowledge_llm_rerank, get_agent
from ai_native_core.model import last_model

# from settings import langsmith_token
#
# os.environ["LANGSMITH_TRACING"] = "true"
# os.environ["LANGSMITH_API_KEY"] = langsmith_token


chat_bot_template = ChatPromptTemplate.from_messages(
    [
        {
            "role": "system",
            "content": '''{prompt}''',
        }
    ]
)


async def query_analysis(state: State, config):
    """分析用户的问题"""
    # 这里可以添加一些问题分析的逻辑
    # 比如判断问题的类型,是否需要使用RAG等
    return {
        "messages": {
            "role": "human",
            "content": state["question"],
        }
    }


async def generate(state: State, config):
    configuration = Configuration.from_runnable_config(config)
    if configuration.rag_config.is_rag:
        context = state["context"]
        rag_knowledge_context = get_rag_knowledge_context(context)
        # RAG每次的系统消息都要重新生成,所以不进入状态机的管理
        messages = rag_prompt_template.invoke(
            {
                "context": rag_knowledge_context,
                "prompt": configuration.rag_config.prompt
            }
        )
        messages.messages.extend(state["messages"])
        if configuration.rag_config.is_structured_output:
            rag_model_with_structured_output = last_model.with_structured_output(
                RAGAnswer,
            )
        else:
            rag_model_with_structured_output = last_model
        if configuration.tool_config.is_rag and state['tool_context']:
            prompt_prefix = messages.messages[0].content
            agent = get_agent(state, prompt_prefix)
            response = await agent.ainvoke(
                {
                    "messages": state["messages"],
                    "recursion_limit": 2 * configuration.tool_config.max_iterations + 1
                }
            )
            return {
                "answer": response['messages'][-1].content,
                "messages": response['messages']
            }
        else:
            response = await rag_model_with_structured_output.ainvoke(messages)
            return {
                "answer": response.answer,
                "messages": AIMessage(content=response.answer)
            }
    else:
        # 聊天机器人系统消息每次动态生成,不尼禄状态机管理
        messages = chat_bot_template.invoke(
            {
                "prompt": configuration.chat_bot_config.prompt
            }
        )
        # 将用户的问题以及上下文信息添加到消息中
        messages.messages.extend(state["messages"])
        if configuration.tool_config.is_rag and state['tool_context']:
            prompt_prefix = configuration.chat_bot_config.prompt
            agent = get_agent(state, prompt_prefix)
            response = await agent.ainvoke(
                {
                    "messages": state["messages"],
                    "recursion_limit": 2 * configuration.tool_config.max_iterations + 1
                }
            )
            return {
                "answer": response['messages'][-1].content,
                "messages": response['messages']
            }
        else:
            response = await last_model.ainvoke(messages)
            return {
                "answer": response.content,
                "messages": response
            }


async def delete_messages(state: State, config):
    messages = state["messages"]
    configuration = Configuration.from_runnable_config(config)
    # 删除多余的消息,自动化管理消息,发出删除消息的信号
    to_keep_messages = trim_messages(
        messages,
        # Keep the last <= n_count tokens of the messages.
        # 保留最后 <= n_count 个 token 的消息
        strategy="last",
        # token计算器
        token_counter=count_tokens_approximately,
        # 最大token数，防止上下文信息太长导致信息爆炸
        max_tokens=configuration.memory_config.max_tokens,
        # 开始聊天的时候总是从human的角色开始
        start_on="human",
        end_on=("ai", "tool"),
        # trim消息的时候必须保留system中的提示词
        include_system=False,
        allow_partial=False,
    )
    to_delete_messages = [
        m for m in messages if m not in to_keep_messages
    ]
    if to_delete_messages:
        return {"messages": [RemoveMessage(id=m.id) for m in to_delete_messages]}
    return None


# TODO: 多轮对话messages状态合理化管理

graph_builder = (StateGraph(
    state_schema=State,
    config_schema=Configuration,
    input=InputState,
    output=OutputState
)
.add_sequence(
    [
        query_analysis,
        common_knowledge_retrieve,
        common_knowledge_rerank,
        common_knowledge_llm_rerank,
        generate,
        delete_messages,
    ]
).add_sequence(
    [
        tool_knowledge_retrieve,
        tool_knowledge_rerank,
        tool_knowledge_llm_rerank
    ]
).add_edge(
    START, "query_analysis"
).add_edge(
    "query_analysis", "tool_knowledge_retrieve"
).add_edge(
    "tool_knowledge_llm_rerank", "generate"
).add_edge(
    "delete_messages", END
)
)

# Add memory
memory = MemorySaver()
graph = graph_builder.compile(
    # checkpointer=memory,
    name="KnowledgeLLMOpsGraph",
)
