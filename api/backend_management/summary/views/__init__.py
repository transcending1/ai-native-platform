import importlib
import pkgutil

package = importlib.import_module(__name__)
for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__):
    importlib.import_module(f'{package.__name__}.{module_name}')

# 显式导入视图类
from .summary import UserSummaryViewSet, PlatformSummaryViewSet

__all__ = ['UserSummaryViewSet', 'PlatformSummaryViewSet']
