from django.db import models


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
