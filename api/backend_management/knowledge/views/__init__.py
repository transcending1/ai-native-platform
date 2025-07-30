import pkgutil
import importlib

package = importlib.import_module(__name__)
for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__):
    importlib.import_module(f'{package.__name__}.{module_name}')

from .namespace import NamespaceViewSet
from .knowledge_management import KnowledgeDocumentViewSet

__all__ = [
    'NamespaceViewSet',
    'KnowledgeDocumentViewSet'
]
