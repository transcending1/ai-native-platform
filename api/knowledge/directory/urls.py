# # # from django.urls import path
# # # from . import views
# # #
# # # urlpatterns = [
# # #     path('namespaces/', views.NamespaceListCreateView.as_view()),
# # #     path('namespaces/<int:namespace_id>/directories/', views.NamespaceDirectoryView.as_view()),
# # #     path('directories/<int:pk>/', views.DirectoryDetailView.as_view()),
# # # ]
# # from rest_framework.routers import DefaultRouter
# # from .views import NamespaceViewSet, DirectoryViewSet, DocumentViewSet
# #
# # router = DefaultRouter()
# # router.register(r'namespaces', NamespaceViewSet, basename='namespace')
# # router.register(r'directories', DirectoryViewSet, basename='directory')
# # router.register(r'documents', DocumentViewSet, basename='document')
# #
# # urlpatterns = router.urls
#
# from django.urls import path, include
# from rest_framework_nested import routers
# from . import views
#
# router = routers.DefaultRouter()
# router.register(r'namespaces', views.NamespaceViewSet)
#
# # 命名空间下的嵌套路由
# namespace_router = routers.NestedSimpleRouter(
#     router, r'namespaces', lookup='namespace'
# )
# namespace_router.register(r'categories', views.CategoryViewSet, basename='namespace-categories')
#
# # 目录下的嵌套路由
# category_router = routers.NestedSimpleRouter(
#     namespace_router, r'categories', lookup='category'
# )
# category_router.register(r'notes', views.NoteViewSet, basename='category-notes')
#
# urlpatterns = [
#     path('', include(router.urls)),
#     path('', include(namespace_router.urls)),
#     path('', include(category_router.urls)),
#
#     # 目录移动端点
#     path(
#         'namespaces/<int:namespace_pk>/categories/<int:pk>/move/',
#         views.CategoryViewSet.as_view({'post': 'move'}),
#         name='category-move'
#     ),
#
#     # 笔记置顶端点
#     path(
#         'namespaces/<int:namespace_pk>/categories/<int:category_pk>/notes/<int:pk>/toggle_pin/',
#         views.NoteViewSet.as_view({'patch': 'toggle_pin'}),
#         name='note-toggle-pin'
#     ),
# ]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'namespaces', views.NamespaceViewSet)
router.register(r'directories', views.DirectoryViewSet)
router.register(r'notes', views.NoteViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # 自定义端点
    path('directories/tree/<int:namespace_id>/',
         views.DirectoryViewSet.as_view({'get': 'namespace_tree'}),
         name='directory-tree'),
]