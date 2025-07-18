from pymilvus import MilvusClient, exceptions
from settings import host

# ——————————————
# 1. 连接 Milvus Standalone
# ——————————————
# 初始化 Milvus 客户端连接
# uri: 连接字符串，格式为"协议+地址+端口"，默认 http://localhost:19530
# token: 认证信息，格式为"用户名:密码"，默认 root:Milvus
# 应用场景：所有 Milvus 操作前必须建立连接，生产环境建议使用更安全的认证方式
client = MilvusClient(
    uri=f"http://{host}:19530",
    token="root:Milvus"
)

# ——————————————
# 2. 创建数据库 my_database_1（无额外属性）
# ——————————————
# 创建基础数据库，不设置任何额外属性
# 应用场景：当只需要基础数据库功能时使用
# AlreadyExistError 处理：防止重复创建导致报错
try:
    client.create_database(db_name="my_database_1")
    print("✓ my_database_1 创建成功")
except exceptions.AlreadyExistError:
    print("ℹ my_database_1 已存在")

# ——————————————
# 3. 创建数据库 my_database_2（设置副本数为 3）
# ——————————————
# 创建带副本配置的数据库
# database.replica.number：设置数据副本数量，3表示每个数据会保存3份
# 副本数意义：提高系统容错能力，当某个节点故障时仍有备份数据可用
# 应用场景：高可用需求场景，如生产环境、关键业务数据
# 注意：副本数增加会消耗更多存储资源，需要权衡可用性和成本
client.create_database(
    db_name="my_database_2",
    properties={"database.replica.number": 3}
)
print("✓ my_database_2 创建成功，副本数=3")

# ——————————————
# 4. 列出所有数据库
# ——————————————
# 获取当前 Milvus 实例中的所有数据库列表
# 应用场景：系统管理、数据库维护时查看现有数据库
db_list = client.list_databases()
print("当前所有数据库：", db_list)

# ——————————————
# 5. 查看默认数据库（default）详情
# ——————————————
# 获取数据库的详细配置信息
# 应用场景：查看数据库配置、排查问题时使用
# default 数据库：Milvus 自动创建的默认数据库，包含基础配置
default_info = client.describe_database(db_name="default")
print("默认数据库详情：", default_info)

# ——————————————
# 6. 修改 my_database_1 属性：限制最大集合数为 10
# ——————————————
# 动态修改数据库属性
# database.max.collections：限制该数据库允许创建的最大集合数量
# 应用场景：资源配额管理，防止单个数据库占用过多资源
# 注意：修改属性会立即生效，可能影响正在进行的操作
client.alter_database_properties(
    db_name="my_database_1",
    properties={"database.max.collections": 10}
)
print("✓ 已为 my_database_1 限制最大集合数为 10")

# ——————————————
# 7. 删除 my_database_1 的 max.collections 限制
# ——————————————
# 移除数据库的特定属性配置
# 应用场景：当不再需要限制时恢复默认设置
# 注意：删除属性后，该配置将恢复系统默认值（通常是无限制）
client.drop_database_properties(
    db_name="my_database_1",
    property_keys=["database.max.collections"]
)
print("✓ 已移除 my_database_1 的最大集合数限制")

# ——————————————
# 8. 切换到 my_database_2（后续所有操作都作用于该库）
# ——————————————
# 设置当前操作的上下文数据库
# 应用场景：多数据库环境下指定操作目标库
# 注意：切换后所有集合操作（create/drop等）都将在该数据库执行
client.use_database(db_name="my_database_2")
print("✓ 已切换当前数据库为 my_database_2")

# ——————————————
# 9. 删除数据库 my_database_2
#    （注意：如果库内有 Collection，需先 client.drop_collection() 将其清空）
# ——————————————
# 永久删除数据库及其所有数据
# 应用场景：清理测试环境、释放存储空间
# 重要警告：
# 1. 删除前必须确保数据库为空（需手动删除所有集合）
# 2. 删除操作不可逆，生产环境需谨慎执行
# 3. 建议先备份重要数据
client.drop_database(db_name="my_database_2")
print("✓ my_database_2 已删除")

# ——————————————
# 10. 删除数据库 my_database_1
# ——————————————
# 删除最后一个示例数据库
# 应用场景：清理演示环境，恢复初始状态
client.drop_database(db_name="my_database_1")
print("✓ my_database_1 已删除")

# 最佳实践提示：
# 1. 生产环境建议设置适当的副本数（通常3-5）
# 2. 重要操作（如删除）建议添加确认流程
# 3. 数据库属性修改可能影响性能，建议在低峰期操作
# 4. 多租户系统可以通过数据库实现资源隔离