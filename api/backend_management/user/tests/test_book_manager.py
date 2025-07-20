import allure
import pytest

from user.models.book_manager import User, Bookstore, Book, PurchaseRecord, PurchaseItem


@allure.feature('用户管理')
@allure.story('创建用户')
@pytest.mark.django_db
def test_create_user():
    with allure.step("创建一个新的用户"):
        user = User.objects.create(name='John Doe', email='john.doe@example.com')
    with allure.step("验证用户信息"):
        assert user.name == 'John Doe'
        assert user.email == 'john.doe@example.com'


@allure.feature('书店管理')
@allure.story('创建书店')
@pytest.mark.django_db
def test_create_bookstore():
    with allure.step("创建一个新的书店"):
        bookstore = Bookstore.objects.create(name='Central Bookstore', website='https://centralbooks.com')
    with allure.step("验证书店信息"):
        assert bookstore.name == 'Central Bookstore'
        assert bookstore.website == 'https://centralbooks.com'


@allure.feature('书籍管理')
@allure.story('创建书籍')
@pytest.mark.django_db
def test_create_book():
    with allure.step("首先创建一个书店"):
        bookstore = Bookstore.objects.create(name='Downtown Bookstore', website='https://downtownbooks.com')
    with allure.step("创建一本书"):
        book = Book.objects.create(title='Django for Beginners', price=29.99, bookstore=bookstore)
    with allure.step("验证书籍信息"):
        assert book.title == 'Django for Beginners'
        assert book.price == 29.99
        assert book.bookstore == bookstore


@allure.feature('购买流程')
@allure.story('用户发起购买')
@pytest.mark.django_db
def test_initiate_purchase():
    with allure.step("创建用户、书店和书籍"):
        user = User.objects.create(name='Alice Smith', email='alice.smith@example.com')
        bookstore = Bookstore.objects.create(name='Uptown Bookstore', website='https://uptownbooks.com')
        book1 = Book.objects.create(title='Python Essentials', price=39.99, bookstore=bookstore)
        book2 = Book.objects.create(title='Advanced Django', price=49.99, bookstore=bookstore)
    with allure.step("定义购物车内容"):
        cart = [
            {'bookId': book1.id, 'quantity': 2},
            {'bookId': book2.id, 'quantity': 1},
        ]
    with allure.step("用户发起购买并生成购买记录"):
        purchase_details = user.initiate_purchase(bookstore_id=bookstore.id, cart=cart)
    with allure.step("验证购买详情"):
        assert purchase_details['status'] == 'Confirmed'
        assert purchase_details['totalAmount'] == 2 * book1.price + 1 * book2.price
    with allure.step("验证购买记录在数据库中存在"):
        purchase_record = PurchaseRecord.objects.get(id=purchase_details['purchaseId'])
        assert purchase_record.user == user
        assert purchase_record.bookstore == bookstore
        assert purchase_record.totalAmount == purchase_details['totalAmount']
    with allure.step("验证购买项在数据库中存在"):
        purchase_items = PurchaseItem.objects.filter(purchaseRecord=purchase_record)
        assert purchase_items.count() == 2
        item1 = purchase_items.get(book=book1)
        item2 = purchase_items.get(book=book2)
        assert item1.quantity == 2
        assert item1.unitPrice == book1.price
        assert item2.quantity == 1
        assert item2.unitPrice == book2.price


@allure.feature('购买流程')
@allure.story('用户发起购买时书店不存在')
@pytest.mark.django_db
def test_initiate_purchase_with_invalid_bookstore():
    with allure.step("创建用户和书籍，但不创建书店"):
        user = User.objects.create(name='Bob Johnson', email='bob.johnson@example.com')
        bookstore_id = 999  # 非存在的书店ID
        cart = []
    with allure.step("尝试发起购买并验证异常"):
        with pytest.raises(Bookstore.DoesNotExist):
            user.initiate_purchase(bookstore_id=bookstore_id, cart=cart)


@allure.feature('购买流程')
@allure.story('用户发起购买时书籍不存在')
@pytest.mark.django_db
def test_initiate_purchase_with_invalid_books():
    with allure.step("创建用户和书店"):
        user = User.objects.create(name='Carol White', email='carol.white@example.com')
        bookstore = Bookstore.objects.create(name='Eastside Bookstore', website='https://eastsidebooks.com')
    with allure.step("定义购物车中包含不存在的书籍ID"):
        cart = [
            {'bookId': 999, 'quantity': 1},  # 非存在的书籍ID
        ]
    with allure.step("尝试发起购买并验证异常"):
        with pytest.raises(Book.DoesNotExist):
            user.initiate_purchase(bookstore_id=bookstore.id, cart=cart)


@allure.feature('购买流程')
@allure.story('批量创建购买项')
@pytest.mark.django_db
def test_bulk_create_purchase_items():
    with allure.step("创建用户、书店和多个书籍"):
        user = User.objects.create(name='David Lee', email='david.lee@example.com')
        bookstore = Bookstore.objects.create(name='Westside Bookstore', website='https://westsidebooks.com')
        books = [
            Book.objects.create(title='Book One', price=19.99, bookstore=bookstore),
            Book.objects.create(title='Book Two', price=24.99, bookstore=bookstore),
            Book.objects.create(title='Book Three', price=29.99, bookstore=bookstore),
        ]
    with allure.step("定义购物车内容"):
        cart = [
            {'bookId': books[0].id, 'quantity': 1},
            {'bookId': books[1].id, 'quantity': 3},
            {'bookId': books[2].id, 'quantity': 2},
        ]
    with allure.step("用户发起购买并生成购买记录"):
        purchase_details = user.initiate_purchase(bookstore_id=bookstore.id, cart=cart)
    with allure.step("验证批量创建的购买项数量"):
        purchase_record = PurchaseRecord.objects.get(id=purchase_details['purchaseId'])
        purchase_items = PurchaseItem.objects.filter(purchaseRecord=purchase_record)
        assert purchase_items.count() == 3
    with allure.step("验证每个购买项的正确性"):
        for item in purchase_items:
            corresponding_cart_item = next((c for c in cart if c['bookId'] == item.book.id), None)
            assert corresponding_cart_item is not None
            assert item.quantity == corresponding_cart_item['quantity']
            assert item.unitPrice == item.book.price


@allure.feature('购买流程')
@allure.story('购买事务的原子性')
@pytest.mark.django_db
def test_purchase_transaction_atomicity():
    with allure.step("创建用户和书店"):
        user = User.objects.create(name='Eve Black', email='eve.black@example.com')
        bookstore = Bookstore.objects.create(name='Northside Bookstore', website='https://northsidebooks.com')
    with allure.step("定义购物车，其中一个书籍ID无效以触发异常"):
        cart = [
            {'bookId': 1, 'quantity': 1},  # 假设此ID存在
            {'bookId': 999, 'quantity': 1},  # 非存在的书籍ID
        ]
        # 创建一个有效书籍
        valid_book = Book.objects.create(title='Valid Book', price=15.99, bookstore=bookstore)
        cart[0]['bookId'] = valid_book.id
    with allure.step("尝试发起购买并验证事务回滚"):
        with pytest.raises(Book.DoesNotExist):
            user.initiate_purchase(bookstore_id=bookstore.id, cart=cart)
    with allure.step("验证没有购买记录被创建"):
        assert not PurchaseRecord.objects.filter(user=user, bookstore=bookstore).exists()
    with allure.step("验证没有购买项被创建"):
        assert not PurchaseItem.objects.exists()
