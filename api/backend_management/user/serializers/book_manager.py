from rest_framework import serializers
from user.models.book_manager import User, Bookstore, Book, PurchaseRecord, PurchaseItem


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class BookstoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookstore
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class PurchaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseItem
        fields = '__all__'


class PurchaseRecordSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseRecord
        fields = '__all__'