import allure
import pytest

from user.models.book_manager import Bookstore, Book


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
