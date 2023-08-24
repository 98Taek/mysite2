from _decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from shop.forms import OrderCreateForm
from shop.models import Product, OrderItem
from shop.tasks import order_created


def add_cart(request):
    product_id = request.POST.get('id')
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    cart[str(product_id)] = {
        'product_id': str(product_id),
        'quantity': 1,
        'price': str(product.price),
    }
    request.session['cart'] = cart
    request.session.modified = True
    return JsonResponse({'cart_length': len(cart.items())})


def cart_detail(request):
    cart = request.session.get('cart', {})
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    for product in products:
        cart[str(product.id)]['product'] = product
    for key, item in cart.items():
        item['price'] = Decimal(item['price'])
        item['total_price'] = item['price'] * item['quantity']
        cart[key] = item
    total_price = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())
    return render(request, 'shop/cart.html', {'cart_dict': cart, 'total_price': total_price})


def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    del cart[str(product_id)]
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('shop:cart_detail')


def cart_update(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)]['quantity'] = Decimal(request.POST.get('quantity'))
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('shop:cart_detail')


def order_create(request):
    cart = request.session.get('cart', {})
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    for product in products:
        cart[str(product.id)]['product'] = product
    for key, item in cart.items():
        item['price'] = Decimal(item['price'])
        item['total_price'] = item['price'] * item['quantity']
        cart[key] = item
    total_price = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())

    if len(cart.keys()) == 0:
        return redirect('blog:post_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart.values():
                product = cart[item['product_id']]['product']
                item['price'] = Decimal(product.price)
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'],
                                         quantity=item['quantity'])
            request.session['cart'] = {}
            request.session.modified = True
            order_created.delay(order.id)
            return render(request, 'shop/payment.html', {'order': order})
    else:
        form = OrderCreateForm()

    return render(request, 'shop/new_order.html', {'form': form, 'cart_dict': cart, 'total_price': total_price})


def payment_success(request):
    payment_key = request.GET.get('paymentKey')
    order_id = request.GET.get('orderId')
    res = dict(request.GET.items())
    return render(request, 'shop/success.html', {'paymentKey': payment_key, 'orderId': order_id, 'res': res})


def payment_fail(request):
    code = request.GET.get('code')
    message = request.GET.get('message')
    res = dict(request.GET.items())
    return render(request, 'shop/fail.html', {'code': code, 'message': message, 'res': res})
