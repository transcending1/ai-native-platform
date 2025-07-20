from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from user.models.book_manager import User, Bookstore, Book, PurchaseRecord, PurchaseItem
from user.serializers.book_manager import (
    UserSerializer,
    BookstoreSerializer,
    BookSerializer,
    PurchaseRecordSerializer,
    PurchaseItemSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    filterset_fields = ['email']

    @action(detail=True, methods=['post'])
    def initiate_purchase(self, request, pk=None):
        user = self.get_object()
        bookstore_id = request.data.get('bookstore_id')
        cart = request.data.get('cart', [])

        if not bookstore_id or not isinstance(cart, list):
            return Response(
                {"detail": "Invalid bookstore_id or cart data."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = user.initiate_purchase(bookstore_id, cart)
            return Response(result, status=status.HTTP_201_CREATED)
        except Bookstore.DoesNotExist:
            return Response(
                {"detail": "Bookstore not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Book.DoesNotExist as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": "An error occurred during purchase initiation."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
