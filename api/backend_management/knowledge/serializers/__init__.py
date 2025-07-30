import pkgutil
import importlib

package = importlib.import_module(__name__)
for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__):
    importlib.import_module(f'{package.__name__}.{module_name}')

from .namespace import NamespaceSerializer, NamespaceCollaboratorSerializer
from .knowledge_management import (
    KnowledgeDocumentListSerializer,
    KnowledgeDocumentDetailSerializer,
    KnowledgeDocumentTreeSerializer,
    KnowledgeDocumentCreateSerializer,
    KnowledgeDocumentMoveSerializer,
    KnowledgeDocumentToolSerializer,
    KnowledgeDocumentFormSerializer,
    FormDataEntrySerializer,
    ToolExecutionSerializer,
    ToolDataSerializer,
    FormDataSerializer,
    FormFieldSerializer,
    UserSimpleSerializer
)

__all__ = [
    'NamespaceSerializer',
    'NamespaceCollaboratorSerializer',
    'KnowledgeDocumentListSerializer',
    'KnowledgeDocumentDetailSerializer',
    'KnowledgeDocumentTreeSerializer',
    'KnowledgeDocumentCreateSerializer',
    'KnowledgeDocumentMoveSerializer',
    'KnowledgeDocumentToolSerializer',
    'KnowledgeDocumentFormSerializer',
    'FormDataEntrySerializer',
    'ToolExecutionSerializer',
    'ToolDataSerializer',
    'FormDataSerializer',
    'FormFieldSerializer',
    'UserSimpleSerializer'
]
