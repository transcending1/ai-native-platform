# 知识库管理系统需求描述

## 项目路径
1. APP路径:api/backend_management/knowledge
2. APP下面的子模块名称: namespace
3. 用户APP模型的路径：/api/backend_management/user/models/user.py  你可以参考用户模型进行外键建模
4. API文档路径：api_schema.yaml（你去看一下就知道怎么对接服务端）
5. Web端APP子项目: new_web/src/views/KnowledgeNamespace
6. Web端左侧菜单栏（Sidebar）：new_web/src/components/Sidebar.vue


## 第一版需求
1.左侧菜单栏增加知识管理选项，点击后可以跳转到知识管理界面。
2.进入知识管理界面，可以创建Namespace（一个知识库就是一个Namespace的概念）。知识库由个人用户进行创建，也可以邀请其他用户进行协作。（列表中只能看到用户自己创建的知识库以及被其他用户邀请协作的知识库）
3.点击右上角有新建知识库的能力。点击了之后，输入知识库名称，简介，还可以设定什么人可以访问。默认就是协助者可以访问，还可以公开让所有人访问。（所有人访问不是让互联网所有人可以去访问，而是让管理系统里面激活的用户可以访问。）
4.可以通过名字搜索知识库。
5.知识库的基础信息可以点击按钮编辑。重命名，权限修改，更多设置，删除。
6.点击更多设置可以进入知识库管理界面（仅仅需要实现两个功能即可：1.知识库基本信息的编辑设置 2.知识库权限的管理，可以添加协作用户），里面的添加可以根据用户名（username）去添加用户，让对应的用户进入协同编辑模式。
7.知识库的基本信息可以在知识库管理界面进行编辑（包括知识库的封面）
8.邀请协助者来管理知识库一共有两种类型的权限：
    1.管理权限
    2.只读权限，并且都可以在设置中更改。只读权限的用户只能查看知识库，不能编辑知识库的配置。不能编辑里面的文章。

### 第一版迭代目录结构
new_web/src/
├── api.js                                    # 新增知识库API方法
├── components/Sidebar.vue                    # 修改：添加知识管理菜单
├── router/index.js                          # 修改：添加路由配置
└── views/KnowledgeNamespace/
    ├── Main.vue                             # 主页面
    └── components/
        ├── CreateNamespaceDialog.vue        # 新建知识库对话框
        └── NamespaceSettingsDialog.vue      # 知识库设置对话框

