# Bot管理需求描述

## 项目路径

1. APP路径:api/backend_management/bot
2. APP下面的子模块名称: bot
3. 用户APP模型的路径：/api/backend_management/user/models/user.py 你可以参考用户模型进行外键建模
4. Web端APP子项目: new_web/src/views/Bot Bot组件: new_web/src/views/Bot/components/*
5. Web端左侧菜单栏（Sidebar）：new_web/src/components/Sidebar.vue

# 第一版需求

1.左侧菜单栏增加知识管理选项，点击后可以跳转到Assistants管理界面（机器人助手管理界面）。
2.进入Assistants界面，可以创建Assistants（一个Assistant就是一个Bot的概念）。Assistant由个人用户进行创建，也可以邀请其他用户进行协作。（列表中只能看到用户自己创建的Assistant以及被其他用户邀请协作的Assistant）
3.点击右上角有新建Assistant的能力。点击了之后，输入Assistant名称，简介，还可以设定什么人可以访问。默认就是协助者可以访问，还可以公开让所有人访问。（所有人访问不是让互联网所有人可以去访问，而是让管理系统里面激活的用户可以访问。）
4.可以通过名字，所属人搜索Assistant，还可以分页，按照创建时间排序展示。
5.Assistant的基础信息可以点击按钮编辑。重命名，权限修改，更多设置，删除。
6.点击更多设置可以进入Assistant管理界面（仅仅需要实现两个功能即可：1.知识库基本信息的编辑设置
2.Assistant权限的管理，可以添加协作用户），里面的添加可以根据用户名（username）去添加用户，让对应的用户进入协同编辑模式。
7.Assistant的基本信息可以在Assistant管理界面进行编辑（包括Assistant的封面）
8.邀请协助者来管理Assistant一共有两种类型的权限：
1.管理权限
2.只读权限，并且都可以在设置中更改。只读权限的用户只能查看Assistant，不能编辑Assistant的配置。不能编辑里面的文章。


## 风格迁移（你需要借鉴知识库Namespace管理的逻辑来构建服务端的逻辑+Web前端的逻辑）
### 你需要参考NameSpace管理Web端目录结构去构建Web前端项目
new_web/src/
├── api.js                                    # 新增知识库API方法
├── components/Sidebar.vue                    # 修改：添加知识管理菜单
├── router/index.js                          # 修改：添加路由配置
└── views/KnowledgeNamespace/
    ├── Main.vue                             # 主页面
    └── components/
        ├── CreateNamespaceDialog.vue        # 新建知识库对话框
        └── NamespaceSettingsDialog.vue      # 知识库设置对话框

### NameSpace管理服务端目录结构去构建服务端项目
api/backend_management/knowledge/
├── models/
│   ├── namespace.py                          # Namespace模型
├── views/
│   ├── namespace_view.py                     # Namespace视图
├── serializers/
│   ├── namespace.py                          # Namespace序列化&反序列化器

## 服务端API参考
+ 通过外部LangGraph的接口去管理Bot CRUD的基本操作
+ 参考接口: api/backend_management/core/extensions/tests/integration_tests/test_langgraph_sdk.py
+ 细节1：调用创建Assistant接口的时候metadata需要传入一些字段:1.用户id 2.创建时间 3.更新时间。
+ 细节2：调用创建Assistant接口的时候不需要传入config。更新的时候传入config即可。(在详情页中才考虑更新config的逻辑，在此处不考虑更新config)
+ 细节3：调用创建Assistant接口的时候需要传入description（选填）,name（必填）。在外部整体视图中只需要更新name和description即可。不需要更新config。
+ 细节4：你需要给机器人传递一个头像，上传的方式可以给 Assistant 创建一个头像。并存储在metadata里面
+ 细节5: 这个界面你要支持Assistant的搜索功能：通过测试用例中：获取Assistants列表 里面的方式通过元数据过滤，通过创建时间排序，分页展示的能力需要支持
+ 细节6：你忽略 测试用例里面的 进入调试界面创建测试Thread/第一轮对话:发送消息到Assistants/第二轮对话:发送消息到Assistants,证明有记忆力/下次点击调试的时候或者用户点击情况的时候重新创建测试thread 这些功能即可。这些功能要到后续才能用到。
+ 细节7：你还需要支持 删除Assistants 的能力。测试用例里面的接口可以参考。


# 第一版迭代目录结构
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