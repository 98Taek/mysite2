from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

from blog.models import Post


class Product(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(max_length=200),
        currency=models.CharField(max_length=3),
        price=models.DecimalField(default=0, max_digits=12, decimal_places=2),
        description=models.TextField(blank=True),
    )
    posts = models.ManyToManyField(Post, related_name='products')
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return self.name


class Order(models.Model):
    name = models.CharField(_('name'), max_length=50)
    email = models.EmailField(_('email'))
    address = models.CharField(_('address'), max_length=250)
    zipcode = models.CharField(_('zipcode'), max_length=20)
    paid = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    toss_order_id = models.CharField(max_length=50, unique=True, null=True, default=get_random_string(50))

    def __str__(self):
        return f'주문 {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.order.name}님이 주문 아이템 {self.product.name} x {self.quantity}'

    def get_cost(self):
        return self.price * self.quantity
