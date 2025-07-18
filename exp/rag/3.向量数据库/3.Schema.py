# 安装依赖：pip install pymilvus
from pymilvus import MilvusClient, DataType
from settings import host

# ——————————————
# 0. 连接 Milvus
# ——————————————
# 初始化 Milvus 客户端连接
# uri: 连接字符串，格式为"协议+地址+端口"，默认 http://localhost:19530
# token: 认证信息，格式为"用户名:密码"，默认 root:Milvus
# 应用场景：所有 Milvus 操作前必须建立连接
# 安全建议：生产环境应配置HTTPS和ACL访问控制
client = MilvusClient(
    uri=f"http://{host}:19530",
    token="root:Milvus"
)
print("✓ 已连接 Milvus接口")

# ——————————————
# 1. 创建基本 Schema
# ——————————————
# Schema 是集合的数据结构定义，包含：
# - 字段名称和类型
# - 主键设置
# - 向量维度配置
# 应用场景：
#   - 结构化数据存储设计
#   - 数据模型版本控制
# 注意事项：
#   - Schema创建后不可修改字段类型
#   - 字段增删需要通过alter_collection_field
schema = MilvusClient.create_schema()
print("✓ 已创建空 Schema")

# ——————————————
# 2. 添加主键字段（Primary Field）
# ——————————————
# 主键字段是集合中每条数据的唯一标识
# 支持两种主键模式：
# 2.1 手动指定ID（适用于已有业务ID的场景）
schema.add_field(
    field_name="id",
    datatype=DataType.INT64,
    is_primary=True,  # 必须指定一个主键字段
    auto_id=False  # 关闭自动ID生成，需手动提供
)

# 2.2 自动生成ID（适用于无业务ID的场景）
# 典型应用：
#   - 日志数据存储
#   - 无需业务标识的向量数据
# schema.add_field(
#     field_name="doc_id",
#     datatype=DataType.VARCHAR,
#     is_primary=True,
#     auto_id=True,     # 开启自动生成UUID格式ID
#     max_length=100    # VARCHAR必须指定长度
# )
print("✓ 已添加主键字段")

# ——————————————
# 3. 添加向量字段（Vector Field）
# ——————————————
# 3.1 浮点向量（最常用类型）
# 适用场景：
#   - NLP文本嵌入（BERT/GPT等生成的向量）
#   - 图像特征向量
# 性能特点：
#   - 精度高但存储占用较大
#   - 支持L2/IP/COSINE等相似度计算
schema.add_field(
    field_name="text_vector",
    datatype=DataType.FLOAT_VECTOR,
    dim=768  # 需与模型输出维度一致（如BERT-base为768）
)

# 3.2 二进制向量（节省存储空间）
# 适用场景：
#   - 指纹/哈希特征存储
#   - 内存敏感型应用
# 特点：
#   - 只支持汉明距离（Hamming）计算
#   - 维度必须是8的倍数
schema.add_field(
    field_name="image_vector",
    datatype=DataType.BINARY_VECTOR,
    dim=256  # 典型值：64/128/256/512
)
print("✓ 已添加向量字段")

# ——————————————
# 4. 添加标量字段（Scalar Field）
# ——————————————
# 4.1 字符串字段（支持模糊查询）
# 应用场景：
#   - 文档标题/描述文本
#   - 分类标签
schema.add_field(
    field_name="title",
    datatype=DataType.VARCHAR,
    max_length=200,  # 按业务需求设置
    is_nullable=True,
    default_value="untitled"  # 默认值可减少空值处理
)

# 4.2 数值字段（支持范围查询）
# 典型用途：
#   - 年龄/价格等数值属性
#   - 版本号/状态码
schema.add_field(
    field_name="age",
    datatype=DataType.INT32,
    is_nullable=False  # 强制要求提供该字段
)

# 4.3 布尔字段（过滤标记）
# 常见用途：
#   - 启用/禁用状态
#   - 二分类标签
schema.add_field(
    field_name="is_active",
    datatype=DataType.BOOL,
    default_value=True  # 默认激活状态
)

# 4.4 JSON字段（灵活存储结构化数据）
# 优势：
#   - 存储嵌套数据
#   - 无需预定义子字段
# 使用场景：
#   - 用户画像标签
#   - 动态元数据
schema.add_field(
    field_name="metadata",
    datatype=DataType.JSON
)

# 4.5 数组字段（多值属性）
# 典型应用：
#   - 商品多分类
#   - 用户兴趣标签
schema.add_field(
    field_name="tags",
    datatype=DataType.ARRAY,
    element_type=DataType.VARCHAR,
    max_capacity=10,  # 限制数组元素数量
    max_length=50  # 限制每个字符串长度
)
print("✓ 已添加标量字段")

# ——————————————
# 5. 添加动态字段（Dynamic Field）
# ——————————————
# 动态字段特性：
# - 允许插入未定义的字段
# - 自动存储为JSON格式
# 适用场景：
#   - 快速迭代开发阶段
#   - 不确定的数据结构
# 注意：
#   - 查询性能低于预定义字段
#   - 不支持建索引
# schema.add_field(
#     field_name="dynamic_field",
#     datatype=DataType.VARCHAR,
#     is_dynamic=True,
#     max_length=500
# )
print("✓ 已添加动态字段")

# ——————————————
# 6. 使用Schema创建Collection
# ——————————————
# 将Schema实体化为可操作的集合
# 参数说明：
#   - collection_name: 需唯一
#   - schema: 前面定义的数据结构
# 高级配置：
#   - 可添加shards_num参数设置分片数
#   - 可通过properties设置TTL等属性
collection_name = "document_store10"
client.create_collection(
    collection_name=collection_name,
    schema=schema
)
print(f"✓ 已创建集合 {collection_name}")

# ——————————————
# 7. 修改Collection字段
# ——————————————
# 字段修改限制：
# - 不能修改已有字段的数据类型
# - 只能调整部分参数（如数组容量）
# 典型用途：
#   - 扩容数组字段
#   - 添加新功能字段
# client.alter_collection_field(
#     collection_name=collection_name,
#     field_name="tags",
#     field_params={
#         "max_capacity": 64  # 扩展数组容量
#     }
# )
# print("✓ 已添加新字段")

# ——————————————
# 8. 查看Collection详情
# ——————————————
# 获取集合的完整配置信息，包括：
# - 所有字段定义
# - 自动生成的索引
# - 物理分片信息
# 应用场景：
#   - 调试时验证配置
#   - 自动化部署检查
info = client.describe_collection(collection_name=collection_name)
print("Collection详情：", info)

# ——————————————
# 9. 清理
# ——————————————
# 删除测试集合（生产环境慎用）
# 注意事项：
#   - 会永久删除所有数据
#   - 需要先release已加载的集合
client.drop_collection(collection_name=collection_name)
print("✓ 已删除测试集合")

# 最佳实践建议：
# 1. 主键选择：
#    - 有业务ID用INT64/VARCHAR
#    - 无业务ID用自动生成
# 2. 向量维度：
#    - 与模型输出严格一致
#    - 二进制向量需8的倍数
# 3. 生产环境：
#    - 禁用动态字段
#    - 为查询字段建索引
# 4. 版本控制：
#    - 通过集合命名区分版本
#    - 使用alias实现无缝切换
