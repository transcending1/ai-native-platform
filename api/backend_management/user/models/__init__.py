import pkgutil
import importlib

package = importlib.import_module(__name__)
for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__):
    importlib.import_module(f'{package.__name__}.{module_name}')

from .user import CustomUser
from .book_manager import Bookstore, Book, PurchaseRecord, PurchaseItem

__all__ = ['CustomUser', 'Bookstore', 'Book', 'PurchaseRecord', 'PurchaseItem']
