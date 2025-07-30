from django.urls import include, path
from rest_framework import routers
from rest_framework_nested import routers as nested_routers

from knowledge.views import (
    NamespaceViewSet,
    KnowledgeDocumentViewSet
)

# 主路由 - 知识库
router = routers.DefaultRouter()
router.register(r'namespaces', NamespaceViewSet, basename='namespace')

# 嵌套路由 - 知识库下的文档
namespace_documents_router = nested_routers.NestedDefaultRouter(
    router, r'namespaces', lookup='namespace'
)
namespace_documents_router.register(
    r'documents', KnowledgeDocumentViewSet, basename='namespace-documents'
)

# 合并所有路由
urlpatterns = [
    # 主路由
    path('', include(router.urls)),
    
    # 知识库文档路由
    path('', include(namespace_documents_router.urls)),
]

"""
生成的URL模式示例：

知识库相关：
- GET    /namespaces/                    - 获取知识库列表
- POST   /namespaces/                    - 创建知识库
- GET    /namespaces/{id}/               - 获取知识库详情
- PUT    /namespaces/{id}/               - 更新知识库
- DELETE /namespaces/{id}/               - 删除知识库

文档相关：
- GET    /namespaces/{id}/documents/                    - 获取文档列表
- POST   /namespaces/{id}/documents/                    - 创建文档
- GET    /namespaces/{id}/documents/{doc_id}/           - 获取文档详情
- PUT    /namespaces/{id}/documents/{doc_id}/           - 更新文档
- DELETE /namespaces/{id}/documents/{doc_id}/           - 删除文档
- GET    /namespaces/{id}/documents/tree/               - 获取文档树
- POST   /namespaces/{id}/documents/{doc_id}/move/      - 移动文档
"""
