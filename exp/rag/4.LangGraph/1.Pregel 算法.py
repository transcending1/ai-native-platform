"""
LangGraph 运行时架构模拟实现
基于 Google Pregel 算法的分布式计算模型

核心思想：
Pregel算法的精妙之处在于将复杂的图计算问题转化为"思考-行动-同步"的循环模式
就像一群人在开会讨论问题：
1. 每个人独立思考（Plan阶段）
2. 同时发言表达观点（Execution阶段）  
3. 统一整理所有意见（Update阶段）
4. 进入下一轮讨论

这种模式避免了传统递归调用的复杂性，让异步计算变得简单而优雅。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set, Optional, Callable, Union
from dataclasses import dataclass, field
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum


class ChannelType(Enum):
    """通道类型枚举"""
    LAST_VALUE = "last_value"
    TOPIC = "topic" 
    BINARY_AGGREGATE = "binary_aggregate"


@dataclass
class Message:
    """消息类：在Actor和Channel之间传递的数据载体"""
    sender: str  # 发送者ID
    data: Any    # 消息内容
    timestamp: float = field(default_factory=time.time)


class Channel(ABC):
    """
    通道抽象基类：Actor之间通信的桥梁
    
    精妙之处：
    - 通道不仅仅是数据传递的管道，更是状态管理的容器
    - 不同的聚合策略让复杂的数据融合变得简单
    - 类似现实中的"信息收集箱"，每种箱子有不同的整理规则
    """
    
    def __init__(self, name: str):
        self.name = name
        self.subscribers: Set[str] = set()  # 订阅者列表
        self.pending_updates: List[Message] = []  # 待处理的更新
        self.updated_in_step = False  # 本轮是否有更新
        self._lock = threading.Lock()
    
    def subscribe(self, actor_id: str):
        """Actor订阅此通道"""
        self.subscribers.add(actor_id)
    
    def add_update(self, message: Message):
        """添加待处理的更新（在Execution阶段调用）"""
        with self._lock:
            self.pending_updates.append(message)
    
    @abstractmethod
    def apply_updates(self) -> bool:
        """
        应用所有待处理的更新（在Update阶段调用）
        返回是否有实际更新发生
        """
        pass
    
    @abstractmethod
    def get_current_value(self) -> Any:
        """获取当前通道的值"""
        pass


class LastValueChannel(Channel):
    """
    最后值通道：只保留最后一次写入的值
    
    应用场景：
    - 用户输入
    - 最终输出结果  
    - 状态标志
    
    精妙之处：简单但实用，大多数情况下我们只关心"最新"的状态
    """
    
    def __init__(self, name: str, initial_value: Any = None):
        super().__init__(name)
        self.value = initial_value
    
    def apply_updates(self) -> bool:
        """应用更新：取最后一个消息的值"""
        with self._lock:
            if not self.pending_updates:
                self.updated_in_step = False
                return False
            
            # 按时间排序，取最新的值
            self.pending_updates.sort(key=lambda x: x.timestamp)
            latest_message = self.pending_updates[-1]
            
            old_value = self.value
            self.value = latest_message.data
            
            self.pending_updates.clear()
            self.updated_in_step = True
            
            # 只有值真正改变时才返回True
            return old_value != self.value
    
    def get_current_value(self) -> Any:
        return self.value


class TopicChannel(Channel):
    """
    主题通道：发布-订阅模式，支持多值聚合
    
    应用场景：
    - 多个Agent的建议收集
    - 事件流处理
    - 多源数据融合
    
    精妙之处：像一个"建议收集箱"，可以配置不同的整理策略
    """
    
    def __init__(self, name: str, aggregation_strategy: str = "accumulate"):
        super().__init__(name)
        self.values: List[Any] = []
        self.aggregation_strategy = aggregation_strategy  # "accumulate", "deduplicate"
    
    def apply_updates(self) -> bool:
        """应用更新：根据聚合策略处理多个值"""
        with self._lock:
            if not self.pending_updates:
                self.updated_in_step = False
                return False
            
            new_values = [msg.data for msg in self.pending_updates]
            
            if self.aggregation_strategy == "deduplicate":
                # 去重策略：只添加不重复的值
                for value in new_values:
                    if value not in self.values:
                        self.values.append(value)
            else:  # accumulate
                # 累积策略：添加所有值
                self.values.extend(new_values)
            
            self.pending_updates.clear()
            self.updated_in_step = True
            return len(new_values) > 0
    
    def get_current_value(self) -> List[Any]:
        return self.values.copy()


class BinaryAggregateChannel(Channel):
    """
    二元聚合通道：使用二元操作符累积值
    
    应用场景：
    - 计算总分
    - 统计计数
    - 求平均值
    
    精妙之处：将复杂的聚合计算抽象为简单的二元操作
    """
    
    def __init__(self, name: str, operator: Callable[[Any, Any], Any], initial_value: Any = 0):
        super().__init__(name)
        self.value = initial_value
        self.operator = operator
    
    def apply_updates(self) -> bool:
        """应用更新：使用二元操作符聚合所有新值"""
        with self._lock:
            if not self.pending_updates:
                self.updated_in_step = False
                return False
            
            old_value = self.value
            
            # 对所有新值应用二元操作符
            for message in self.pending_updates:
                self.value = self.operator(self.value, message.data)
            
            self.pending_updates.clear()
            self.updated_in_step = True
            return old_value != self.value
    
    def get_current_value(self) -> Any:
        return self.value


class Actor(ABC):
    """
    Actor抽象基类：实际执行计算的工作单元
    
    精妙之处：
    - 每个Actor都是独立的"专家"，只专注于自己的任务
    - 通过订阅-发布模式与其他Actor解耦
    - 像现实中的"部门"，各司其职，通过"备忘录"沟通
    """
    
    def __init__(self, actor_id: str):
        self.actor_id = actor_id
        self.input_channels: Set[str] = set()
        self.output_channels: Set[str] = set()
    
    def subscribe_to_channel(self, channel_name: str):
        """订阅输入通道"""
        self.input_channels.add(channel_name)
    
    def publish_to_channel(self, channel_name: str):
        """设置输出通道"""
        self.output_channels.add(channel_name)
    
    @abstractmethod
    def can_execute(self, channels: Dict[str, Channel]) -> bool:
        """判断是否可以执行（订阅的通道是否有更新）"""
        pass
    
    @abstractmethod
    def execute(self, channels: Dict[str, Channel]) -> Dict[str, Any]:
        """
        执行计算逻辑
        返回要发送到各个输出通道的消息
        """
        pass


class SimpleActor(Actor):
    """
    简单Actor实现：可配置的计算单元
    
    这是一个通用的Actor实现，可以通过传入函数来定义具体的计算逻辑
    """
    
    def __init__(self, actor_id: str, compute_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        super().__init__(actor_id)
        self.compute_func = compute_func
    
    def can_execute(self, channels: Dict[str, Channel]) -> bool:
        """检查订阅的通道是否有更新"""
        if not self.input_channels:
            return True  # 没有输入通道的Actor总是可以执行（如初始节点）
        
        for channel_name in self.input_channels:
            if channel_name in channels and channels[channel_name].updated_in_step:
                return True
        return False
    
    def execute(self, channels: Dict[str, Channel]) -> Dict[str, Any]:
        """执行计算并返回输出"""
        # 收集输入数据
        inputs = {}
        for channel_name in self.input_channels:
            if channel_name in channels:
                inputs[channel_name] = channels[channel_name].get_current_value()
        
        # 执行计算
        result = self.compute_func(inputs)
        return result if result is not None else {}


class PregelEngine:
    """
    Pregel执行引擎：整个运行时的调度核心
    
    精妙之处解析：
    1. BSP模型的威力：
       - 将复杂的异步计算变成同步的"步进式"执行
       - 每一步都是原子操作，便于调试和理解
       - 天然支持并行计算，利用多核优势
    
    2. 三阶段设计的巧妙：
       - Plan: "谁该工作了？" - 基于数据驱动的调度
       - Execute: "大家一起干活" - 并行执行保证效率  
       - Update: "整理工作成果" - 确保数据一致性
    
    3. 状态管理的艺术：
       - Channel作为状态容器，天然支持版本控制
       - Actor之间完全解耦，只通过Channel通信
       - 支持任意复杂的计算图，而代码保持简洁
    """
    
    def __init__(self, max_steps: int = 100):
        self.channels: Dict[str, Channel] = {}
        self.actors: Dict[str, Actor] = {}
        self.max_steps = max_steps
        self.step_count = 0
        self.execution_history: List[Dict] = []  # 执行历史，便于调试
    
    def add_channel(self, channel: Channel):
        """添加通道到引擎"""
        self.channels[channel.name] = channel
    
    def add_actor(self, actor: Actor):
        """添加Actor到引擎，并建立订阅关系"""
        self.actors[actor.actor_id] = actor
        
        # 建立订阅关系
        for channel_name in actor.input_channels:
            if channel_name in self.channels:
                self.channels[channel_name].subscribe(actor.actor_id)
    
    def run(self, initial_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行Pregel算法的主循环
        
        这就是整个算法的精华所在！
        """
        print("🚀 启动Pregel执行引擎...")
        
        # 初始化输入
        if initial_inputs:
            for channel_name, value in initial_inputs.items():
                if channel_name in self.channels:
                    message = Message(sender="__system__", data=value)
                    self.channels[channel_name].add_update(message)
                    self.channels[channel_name].apply_updates()
        
        while self.step_count < self.max_steps:
            print(f"\n📍 第 {self.step_count + 1} 步执行...")
            
            # ===== 阶段1: Plan - 决定谁该工作 =====
            executable_actors = self._plan_phase()
            if not executable_actors:
                print("✅ 没有更多Actor需要执行，计算完成！")
                break
            
            print(f"🎯 计划执行 Actor: {[actor.actor_id for actor in executable_actors]}")
            
            # ===== 阶段2: Execute - 并行执行 =====
            actor_outputs = self._execute_phase(executable_actors)
            
            # ===== 阶段3: Update - 同步更新 =====
            has_updates = self._update_phase(actor_outputs)
            
            # 记录执行历史
            step_info = {
                "step": self.step_count + 1,
                "executed_actors": [actor.actor_id for actor in executable_actors],
                "channel_states": {name: ch.get_current_value() for name, ch in self.channels.items()},
                "has_updates": has_updates
            }
            self.execution_history.append(step_info)
            
            self.step_count += 1
        
        print(f"\n🏁 执行完成！总共执行了 {self.step_count} 步")
        return {name: ch.get_current_value() for name, ch in self.channels.items()}
    
    def _plan_phase(self) -> List[Actor]:
        """
        Plan阶段：智能调度的核心
        
        精妙之处：
        - 不是简单的轮询，而是基于"数据驱动"的调度
        - 只有当Actor关心的数据发生变化时，才会被唤醒
        - 这种lazy evaluation大大提高了效率
        """
        executable_actors = []
        
        for actor in self.actors.values():
            if actor.can_execute(self.channels):
                executable_actors.append(actor)
        
        return executable_actors
    
    def _execute_phase(self, actors: List[Actor]) -> Dict[str, Dict[str, Any]]:
        """
        Execute阶段：并行计算的艺术
        
        精妙之处：
        - 所有Actor同时执行，真正的并行计算
        - 各自计算过程中看不到其他Actor的中间结果，避免了竞态条件
        - 像一群专家独立工作，最后再汇总结果
        """
        actor_outputs = {}
        
        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=len(actors)) as executor:
            future_to_actor = {
                executor.submit(actor.execute, self.channels): actor 
                for actor in actors
            }
            
            for future in as_completed(future_to_actor):
                actor = future_to_actor[future]
                try:
                    output = future.result()
                    actor_outputs[actor.actor_id] = output
                    print(f"  ✓ {actor.actor_id} 执行完成")
                except Exception as e:
                    print(f"  ❌ {actor.actor_id} 执行失败: {e}")
                    actor_outputs[actor.actor_id] = {}
        
        return actor_outputs
    
    def _update_phase(self, actor_outputs: Dict[str, Dict[str, Any]]) -> bool:
        """
        Update阶段：状态同步的智慧
        
        精妙之处：
        - 统一更新所有Channel，确保下一轮的一致性
        - 支持不同的聚合策略，处理复杂的数据融合场景
        - 原子性操作，要么全部成功，要么全部失败
        """
        # 首先重置所有Channel的更新标志
        for channel in self.channels.values():
            channel.updated_in_step = False
        
        # 收集所有要发送的消息
        for actor_id, outputs in actor_outputs.items():
            actor = self.actors[actor_id]
            for channel_name in actor.output_channels:
                if channel_name in outputs and channel_name in self.channels:
                    message = Message(sender=actor_id, data=outputs[channel_name])
                    self.channels[channel_name].add_update(message)
        
        # 应用所有更新
        has_any_update = False
        for channel in self.channels.values():
            if channel.apply_updates():
                has_any_update = True
                print(f"  📝 {channel.name} 已更新: {channel.get_current_value()}")
        
        return has_any_update
    
    def get_execution_history(self) -> List[Dict]:
        """获取执行历史，便于分析和调试"""
        return self.execution_history


def demo_simple_pipeline():
    """
    演示1：简单的线性处理管道
    
    这个例子展示了最基本的数据处理流程：
    输入 -> 处理1 -> 处理2 -> 输出
    """
    print("=" * 60)
    print("🎬 演示1：简单的数据处理管道")
    print("=" * 60)
    
    # 创建执行引擎
    engine = PregelEngine()
    
    # 创建通道
    input_channel = LastValueChannel("input")
    processed1_channel = LastValueChannel("processed1") 
    output_channel = LastValueChannel("output")
    
    engine.add_channel(input_channel)
    engine.add_channel(processed1_channel)
    engine.add_channel(output_channel)
    
    # 创建处理函数
    def step1_processor(inputs):
        """第一步：将输入数字乘以2"""
        if "input" in inputs:
            result = inputs["input"] * 2
            print(f"    🔄 步骤1: {inputs['input']} × 2 = {result}")
            return {"processed1": result}
        return {}
    
    def step2_processor(inputs):
        """第二步：将结果加10"""
        if "processed1" in inputs:
            result = inputs["processed1"] + 10
            print(f"    🔄 步骤2: {inputs['processed1']} + 10 = {result}")
            return {"output": result}
        return {}
    
    # 创建Actor
    actor1 = SimpleActor("processor1", step1_processor)
    actor1.subscribe_to_channel("input")
    actor1.publish_to_channel("processed1")
    
    actor2 = SimpleActor("processor2", step2_processor)
    actor2.subscribe_to_channel("processed1")
    actor2.publish_to_channel("output")
    
    engine.add_actor(actor1)
    engine.add_actor(actor2)
    
    # 执行计算
    result = engine.run({"input": 5})
    
    print(f"\n🎯 最终结果: {result['output']}")
    print("💡 分析：这个简单的例子展示了Pregel算法如何将串行计算自动并行化")


def demo_parallel_aggregation():
    """
    演示2：并行聚合计算
    
    这个例子展示了多个Actor并行计算并聚合结果的能力：
    多个输入 -> 并行处理 -> 聚合结果
    """
    print("\n" + "=" * 60)
    print("🎬 演示2：并行聚合计算")
    print("=" * 60)
    
    engine = PregelEngine()
    
    # 创建通道
    numbers_channel = TopicChannel("numbers", "accumulate")
    sum_channel = BinaryAggregateChannel("sum", lambda a, b: a + b, 0)
    count_channel = BinaryAggregateChannel("count", lambda a, b: a + b, 0)
    average_channel = LastValueChannel("average")
    
    engine.add_channel(numbers_channel)
    engine.add_channel(sum_channel)
    engine.add_channel(count_channel)
    engine.add_channel(average_channel)
    
    # 创建数据生产者
    def number_generator(actor_id, number):
        def generator(inputs):
            print(f"    📊 {actor_id} 生成数字: {number}")
            return {"numbers": number, "sum": number, "count": 1}
        return generator
    
    # 创建多个数据生产者
    for i, num in enumerate([10, 20, 30, 40, 50]):
        actor = SimpleActor(f"generator_{i}", number_generator(f"生成器{i}", num))
        actor.publish_to_channel("numbers")
        actor.publish_to_channel("sum")
        actor.publish_to_channel("count")
        engine.add_actor(actor)
    
    # 创建平均值计算器
    def average_calculator(inputs):
        if "sum" in inputs and "count" in inputs:
            total_sum = inputs["sum"]
            total_count = inputs["count"]
            if total_count > 0:
                avg = total_sum / total_count
                print(f"    🧮 计算平均值: {total_sum} ÷ {total_count} = {avg}")
                return {"average": avg}
        return {}
    
    avg_actor = SimpleActor("avg_calculator", average_calculator)
    avg_actor.subscribe_to_channel("sum")
    avg_actor.subscribe_to_channel("count")
    avg_actor.publish_to_channel("average")
    engine.add_actor(avg_actor)
    
    # 执行计算
    result = engine.run()
    
    print(f"\n🎯 最终结果:")
    print(f"   所有数字: {result['numbers']}")
    print(f"   总和: {result['sum']}")
    print(f"   数量: {result['count']}")
    print(f"   平均值: {result['average']}")
    print("💡 分析：展示了如何使用不同类型的Channel来处理复杂的并行聚合场景")


def demo_iterative_refinement():
    """
    演示3：迭代优化算法
    
    这个例子展示了Pregel算法在迭代优化中的应用：
    初始值 -> 迭代改进 -> 收敛判断 -> 最终结果
    """
    print("\n" + "=" * 60)
    print("🎬 演示3：迭代优化算法（模拟牛顿法求平方根）")
    print("=" * 60)
    
    engine = PregelEngine(max_steps=10)
    
    # 创建通道
    target_channel = LastValueChannel("target", 25)  # 求25的平方根
    current_guess_channel = LastValueChannel("current_guess", 1.0)  # 初始猜测值
    next_guess_channel = LastValueChannel("next_guess")
    converged_channel = LastValueChannel("converged", False)
    
    engine.add_channel(target_channel)
    engine.add_channel(current_guess_channel) 
    engine.add_channel(next_guess_channel)
    engine.add_channel(converged_channel)
    
    # 牛顿法迭代器
    def newton_iterator(inputs):
        if "target" in inputs and "current_guess" in inputs:
            target = inputs["target"]
            x = inputs["current_guess"]
            
            # 牛顿法公式：x_new = (x + target/x) / 2
            x_new = (x + target / x) / 2
            
            print(f"    🔍 牛顿迭代: x={x:.6f} -> x_new={x_new:.6f}")
            
            # 检查收敛（误差小于0.000001）
            error = abs(x_new - x)
            converged = error < 0.000001
            
            if converged:
                print(f"    ✅ 已收敛！误差: {error:.8f}")
            
            return {
                "next_guess": x_new,
                "converged": converged
            }
        return {}
    
    # 状态更新器
    def state_updater(inputs):
        if "next_guess" in inputs and "converged" in inputs:
            if not inputs["converged"]:  # 只有未收敛时才继续更新
                return {"current_guess": inputs["next_guess"]}
        return {}
    
    # 创建Actor
    iterator_actor = SimpleActor("newton_iterator", newton_iterator)
    iterator_actor.subscribe_to_channel("target")
    iterator_actor.subscribe_to_channel("current_guess")
    iterator_actor.publish_to_channel("next_guess")
    iterator_actor.publish_to_channel("converged")
    
    updater_actor = SimpleActor("state_updater", state_updater)
    updater_actor.subscribe_to_channel("next_guess")
    updater_actor.subscribe_to_channel("converged")
    updater_actor.publish_to_channel("current_guess")
    
    engine.add_actor(iterator_actor)
    engine.add_actor(updater_actor)
    
    # 执行计算
    result = engine.run()
    
    print(f"\n🎯 最终结果:")
    print(f"   目标数字: {result['target']}")
    print(f"   计算结果: {result['current_guess']:.8f}")
    print(f"   真实平方根: {result['target'] ** 0.5:.8f}")
    print(f"   是否收敛: {result['converged']}")
    print("💡 分析：展示了Pregel算法在迭代计算中的威力，自动管理状态转换")


def main():
    """
    主函数：运行所有演示
    
    这些演示展示了Pregel算法的核心优势：
    1. 简洁性：复杂的异步计算变成了简单的步进执行
    2. 并行性：天然支持多核并行，充分利用硬件资源
    3. 可调试性：每一步的状态都清晰可见，便于定位问题
    4. 可扩展性：可以轻松添加新的Actor和Channel
    5. 容错性：单个Actor的失败不会影响整个系统
    """
    print("🌟 LangGraph 运行时架构演示")
    print("基于 Google Pregel 算法的优雅实现")
    print("\n💡 Pregel算法的精妙之处：")
    print("1. 🧠 化繁为简：将复杂的图计算转化为'思考-行动-同步'的循环")
    print("2. ⚡ 天然并行：充分利用多核优势，提升计算效率")
    print("3. 🎯 数据驱动：只有数据变化时才触发计算，避免无效操作")
    print("4. 🔄 状态清晰：每一步的状态都明确可见，便于调试和理解")
    print("5. 🛡️ 解耦设计：Actor之间完全独立，系统健壮性强")
    
    # 运行演示
    demo_simple_pipeline()
    demo_parallel_aggregation()
    demo_iterative_refinement()
    
    print("\n" + "=" * 60)
    print("🎉 所有演示完成！")
    print("💭 总结：Pregel算法将传统的复杂异步编程转化为直观的步进式计算，")
    print("   这种设计让分布式图计算变得简单而优雅。在LangGraph中，")
    print("   这种模式特别适合处理LLM应用中的复杂工作流程。")
    print("=" * 60)


if __name__ == "__main__":
    main()
