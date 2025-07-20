from django.db import models
from django.utils import timezone
from django.db import transaction


class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    def initiate_purchase(self, bookstore_id, cart):
        with transaction.atomic():
            bookstore = Bookstore.objects.get(id=bookstore_id)
            total_amount = sum(item['quantity'] * Book.objects.get(id=item['bookId']).price for item in cart)
            purchase_record = PurchaseRecord.objects.create(
                user=self,
                bookstore=bookstore,
                purchaseDate=timezone.now().date(),
                totalAmount=total_amount
            )
            purchase_items = [
                PurchaseItem(
                    purchaseRecord=purchase_record,
                    book=Book.objects.get(id=item['bookId']),
                    quantity=item['quantity'],
                    unitPrice=Book.objects.get(id=item['bookId']).price
                ) for item in cart
            ]
            PurchaseItem.objects.bulk_create(purchase_items)
            return {
                "purchaseId": purchase_record.id,
                "totalAmount": purchase_record.totalAmount,
                "status": "Confirmed"
            }


class Bookstore(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField()

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    price = models.FloatField()
    bookstore = models.ForeignKey(Bookstore, related_name='books', on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class PurchaseRecord(models.Model):
    user = models.ForeignKey(User, related_name='purchase_records', on_delete=models.CASCADE)
    bookstore = models.ForeignKey(Bookstore, related_name='purchase_records', on_delete=models.CASCADE)
    purchaseDate = models.DateField()
    totalAmount = models.FloatField()


class PurchaseItem(models.Model):
    purchaseRecord = models.ForeignKey(PurchaseRecord, related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unitPrice = models.FloatField()
