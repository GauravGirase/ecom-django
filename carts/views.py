from django.shortcuts import render, redirect,get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from store.models import Product, Variation
from .models import Cart, CartItem


# creating session 
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def get_product_properties(request, product):
    product_variation = []
    for item in request.POST:
        key = item
        value = request.POST.get(key)
        try:
            variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_values__iexact=value)
            product_variation.append(variation)
        except:
            pass
    return product_variation

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == "POST":
        product_variation = get_product_properties(request, product)


    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
        cart.save()

    try:
        # retrive the exiting cart item 
        # if present -> check the tags
        cart_item = CartItem.objects.get(product=product, cart=cart)
        existing_variations = list(cart_item.variations.all())
        if all(var in existing_variations for var in product_variation):
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                cart = cart
            )
            cart_item.variations.add(*product_variation)
            cart_item.quantity += 1
            cart.save()

    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart
        )
        cart_item.variations.add(*product_variation)
        cart_item.quantity += 1
        cart.save()


    return redirect('cart') # url with namespace 'cart'

def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_items = CartItem.objects.filter(product=product, cart=cart)
    product_variation = get_product_properties(request, product)
    for cart_item in cart_items:
        existing_variations = list(cart_item.variations.all())
        if all(var in existing_variations for var in product_variation):
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
    return redirect('cart')

def remove_cart_item(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_items = CartItem.objects.filter(product=product, cart=cart)
    product_variation = get_product_properties(request, product)
    for cart_item in cart_items:
        existing_variations = list(cart_item.variations.all())
        if all(var in existing_variations for var in product_variation):
            cart_item.delete()
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }
    return render(request, 'store/cart.html', context)