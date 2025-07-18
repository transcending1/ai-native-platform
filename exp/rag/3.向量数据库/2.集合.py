# 安装依赖：pip install pymilvus
from pymilvus import MilvusClient
from settings import host

# ——————————————
# 0. 连接 Milvus
# ——————————————
# 初始化 Milvus 客户端连接
# uri: 连接字符串，格式为"协议+地址+端口"，默认 http://localhost:19530
# token: 认证信息，格式为"用户名:密码"，默认 root:Milvus
# 应用场景：所有 Milvus 操作前必须建立连接，生产环境建议配置TLS加密连接
# 注意：Standalone模式适合开发测试，生产环境建议使用Cluster模式
client = MilvusClient(
    uri=f"http://{host}:19530",
    token="root:Milvus"
)
print("✓ 已连接 Milvus接口")

# ——————————————
# 1. 创建 Collection（快速模式）
# ——————————————
# 创建向量集合的快速方法（使用默认配置）
# collection_name: 集合名称（需唯一）
# dimension: 向量维度（必须与后续插入数据维度一致）
# 自动配置：
#   - 使用浮点向量（FloatVector）
#   - 使用欧氏距离（L2）作为相似度度量
#   - 使用IVF_FLAT索引（适合中小规模数据集）
# 应用场景：快速原型开发、概念验证(POC)
collection_name = "quick_setup"

# 先检查并清理可能存在的同名集合（避免冲突）
if collection_name in client.list_collections():
    client.drop_collection(collection_name=collection_name)
    print(f"✓ 已删除已存在的集合 {collection_name}")

# 创建新集合（仅需指定名称和维度）
client.create_collection(
    collection_name=collection_name,
    dimension=5  # 5维向量示例
)
print(f"✓ {collection_name} 已创建")

# ——————————————
# 2. 列出所有 Collections
# ——————————————
# 获取当前数据库中的所有集合列表
# 返回结果包含所有集合名称（字符串列表）
# 应用场景：
#   - 系统管理维护
#   - 检查集合是否存在
#   - 批量操作前的准备工作
cols = client.list_collections()
print("当前所有集合：", cols)

# ——————————————
# 3. 查看 Collection 详情
# ——————————————
# 获取集合的完整配置信息，包括：
# - 向量维度（dimension）
# - 度量类型（metric_type）
# - 自动生成的Schema
# - 当前状态（loaded/released）
# 应用场景：
#   - 调试时查看集合配置
#   - 验证创建参数是否正确
#   - 自动化脚本中获取集合元数据
info = client.describe_collection(collection_name=collection_name)
print(f"{collection_name} 详情：", info)

# ——————————————
# 4. 重命名 Collection
# ——————————————
# 修改集合名称（需确保新名称未被使用）
# 应用场景：
#   - 项目重构时规范命名
#   - 多环境迁移时调整命名空间
#   - A/B测试时标记实验版本
new_collection_name = "quick_renamed"

# 安全检查：删除可能存在的冲突集合
if new_collection_name in client.list_collections():
    client.drop_collection(collection_name=new_collection_name)
    print(f"✓ 已删除已存在的集合 {new_collection_name}")

# 执行重命名操作
client.rename_collection(
    old_name=collection_name,
    new_name=new_collection_name
)
print(f"✓ {collection_name} 已重命名为 {new_collection_name}")

# ——————————————
# 5. 修改 Collection 属性（设置 TTL 60 秒）
# ——————————————
# 动态调整集合配置参数
# collection.ttl.seconds: 生存时间(秒)，到期自动删除数据
# 应用场景：
#   - 临时数据存储（如会话数据）
#   - 自动清理测试数据
#   - 实现数据自动过期策略
# 注意事项：
#   - TTL精度约为10秒级
#   - 删除操作异步执行
client.alter_collection_properties(
    collection_name=new_collection_name,
    properties={"collection.ttl.seconds": 60}
)
print(f"✓ 已为 {new_collection_name} 设置 TTL=60s")

# ——————————————
# 6. 删除 Collection 属性（TTL）
# ——————————————
# 移除已设置的集合属性（恢复默认值）
# 应用场景：
#   - 取消数据自动过期策略
#   - 清理测试配置
# 注意事项：
#   - 删除后该属性将恢复系统默认（无TTL限制）
client.drop_collection_properties(
    collection_name=new_collection_name,
    property_keys=["collection.ttl.seconds"]
)
print(f"✓ 已删除 {new_collection_name} 的 TTL 属性")

# ——————————————
# 7. 加载 & 检查加载状态
# ——————————————
# 将集合加载到内存（必须加载后才能执行搜索/查询）
# 应用场景：
#   - 准备提供服务的集合
#   - 性能测试前的准备工作
# 注意事项：
#   - 加载会消耗内存资源
#   - 大集合加载可能需要较长时间
client.load_collection(collection_name=new_collection_name)
state = client.get_load_state(collection_name=new_collection_name)
print("加载状态：", state)  # 预期输出：<LoadState.Loaded: 1>

# ——————————————
# 8. 释放 & 检查释放状态
# ——————————————
# 从内存卸载集合（释放资源）
# 应用场景：
#   - 长期不用的集合
#   - 资源紧张时释放内存
# 注意事项：
#   - 释放后无法执行搜索/查询
#   - 数据仍持久化在磁盘
client.release_collection(collection_name=new_collection_name)
state = client.get_load_state(collection_name=new_collection_name)
print("释放后状态：", state)  # 预期输出：<LoadState.NotLoad: 0>

# ——————————————
# 9. 管理 Partition
# ——————————————
# Partition（分区）管理：
# - 逻辑上划分集合数据
# - 不同分区可独立加载/释放
# - 支持按分区查询
# 应用场景：
#   - 多租户数据隔离
#   - 按时间/类别划分数据
#   - 热数据/冷数据分离

# 9.1 列出 Partition（默认包含 "_default" 分区）
parts = client.list_partitions(collection_name=new_collection_name)
print("Partition 列表：", parts)

# 9.2 创建新 Partition
client.create_partition(
    collection_name=new_collection_name,
    partition_name="partA"  # 分区名称需唯一
)
print("✓ 已创建 partition partA")
print("更新后 Partition 列表：", client.list_partitions(new_collection_name))

# 9.3 检查 Partition 是否存在
exists = client.has_partition(
    collection_name=new_collection_name,
    partition_name="partA"
)
print("partA 存在？", exists)

# 9.4 加载 & 释放 指定 Partition
# 分区级资源控制，仅加载必要分区
client.load_partitions(
    collection_name=new_collection_name,
    partition_names=["partA"]
)
print("partA 加载状态：",
      client.get_load_state(new_collection_name, partition_name="partA"))

client.release_partitions(
    collection_name=new_collection_name,
    partition_names=["partA"]
)
print("partA 释放后状态：",
      client.get_load_state(new_collection_name, partition_name="partA"))

# 9.5 删除 Partition（需先 release）
# 注意事项：
#   - 分区内数据会被永久删除
#   - 系统分区 "_default" 不可删除
client.drop_partition(
    collection_name=new_collection_name,
    partition_name="partA"
)
print("✓ 已删除 partition partA")
print("最终 Partition 列表：", client.list_partitions(new_collection_name))

# ——————————————
# 10. 管理 Alias
# ——————————————
# Alias（别名）功能：
# - 为集合创建易记的名称
# - 支持动态切换关联集合
# - 实现无缝数据迁移
# 应用场景：
#   - 蓝绿部署
#   - A/B测试流量切换
#   - 版本化数据管理

# 10.1 创建 Alias（一个集合可绑定多个别名）
client.create_alias(collection_name=new_collection_name, alias="alias3")
client.create_alias(collection_name=new_collection_name, alias="alias4")
print("✓ 已创建 alias3, alias4")

# 10.2 列出 Alias
aliases = client.list_aliases(collection_name=new_collection_name)
print("当前 aliases：", aliases)

# 10.3 查看 Alias 详情（返回关联的集合名）
desc = client.describe_alias(alias="alias3")
print("alias3 详情：", desc)

# 10.4 重新分配 Alias（指向新集合）
# 典型应用：将生产流量从v1切换到v2集合
client.alter_alias(collection_name=new_collection_name, alias="alias4")
print("✓ 已将 alias4 重新分配给 quick_renamed")

# 10.5 删除 Alias
client.drop_alias(alias="alias3")
print("✓ 已删除 alias3")
print("剩余 aliases：", client.list_aliases(new_collection_name))

# 10.5 删除 Alias
client.drop_alias(alias="alias4")
print("✓ 已删除 alias3")
print("剩余 aliases：", client.list_aliases(new_collection_name))

# ——————————————
# 11. 删除 Collection
# ——————————————
# 永久删除集合及其所有数据
# 注意事项：
#   - 操作不可逆
#   - 需确保已备份重要数据
#   - 生产环境建议添加确认流程
client.drop_collection(collection_name=new_collection_name)
print(f"✓ 集合 {new_collection_name} 已删除")

# 最佳实践建议：
# 1. 生产环境集合应配置合适的索引（如HNSW）
# 2. 大集合使用分区提高查询效率
# 3. 通过别名实现无缝升级
# 4. 定期监控加载集合的内存使用情况