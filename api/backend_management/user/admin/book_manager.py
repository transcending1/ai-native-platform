from django.contrib import admin
from user.models.book_manager import (
    User,
    Bookstore,
    Book,
    PurchaseRecord,
    PurchaseItem
)


class BookInline(admin.TabularInline):
    model = Book
    extra = 1
    readonly_fields = ('title', 'price')


@admin.register(Bookstore)
class BookstoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name', 'website')
    inlines = [BookInline]


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    readonly_fields = ('book', 'quantity', 'unitPrice')


class PurchaseRecordInline(admin.TabularInline):
    model = PurchaseRecord
    extra = 1
    readonly_fields = ('bookstore', 'purchaseDate', 'totalAmount')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email')
    inlines = [PurchaseRecordInline]


@admin.register(PurchaseRecord)
class PurchaseRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'bookstore', 'purchaseDate', 'totalAmount')
    list_filter = ('bookstore', 'purchaseDate')
    search_fields = ('user__name', 'bookstore__name')
    inlines = [PurchaseItemInline]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'bookstore')
    list_filter = ('bookstore',)
    search_fields = ('title', 'bookstore__name')


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('purchaseRecord', 'book', 'quantity', 'unitPrice')
    list_filter = ('book',)
    search_fields = ('purchaseRecord__id', 'book__title')