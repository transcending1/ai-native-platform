from django.urls import include, path
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from user.views import book_manager
from user.views import big_data

router = routers.DefaultRouter()
router.register(r'user', book_manager.UserViewSet)
router.register(r'bookstore', book_manager.BookstoreViewSet)
router.register(r'book', book_manager.BookViewSet)
router.register(r'k8s', big_data.KubernetesClusterViewSet)
router.register(r'dag', big_data.DAGViewSet)
router.register(r'component', big_data.ComponentViewSet)
router.register(r'task', big_data.TaskViewSet)
router.register(r'log', big_data.LogViewSet)
router.register(r'alert', big_data.AlertViewSet)
router.register(r'billing', big_data.BillingViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('', include(router.urls)),
]
