from rest_framework import viewsets

from user.models.book_manager import Bookstore, Book, PurchaseRecord, PurchaseItem
from user.serializers.book_manager import (
    BookstoreSerializer,
    BookSerializer,
    PurchaseRecordSerializer,
    PurchaseItemSerializer
)


class BookstoreViewSet(viewsets.ModelViewSet):
    queryset = Bookstore.objects.all().order_by('-id')
    serializer_class = BookstoreSerializer
    filterset_fields = ['name', 'website']


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by('-id')
    serializer_class = BookSerializer
    filterset_fields = ['title', 'price', 'bookstore']


class PurchaseRecordViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRecord.objects.all().order_by('-purchaseDate')
    serializer_class = PurchaseRecordSerializer
    filterset_fields = ['user', 'bookstore', 'purchaseDate', 'totalAmount']


class PurchaseItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseItem.objects.all().order_by('-id')
    serializer_class = PurchaseItemSerializer
    filterset_fields = ['purchaseRecord', 'book', 'quantity', 'unitPrice']
