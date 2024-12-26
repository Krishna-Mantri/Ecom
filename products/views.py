from django.shortcuts import render, get_object_or_404,redirect
from django.db.models import Q
from .models import Product, Category

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    
    # Get filter parameters
    query = request.GET.get('q', '')
    min_price = request.GET.get('min', 100)
    max_price = request.GET.get('max', 3000)
    sort_by = request.GET.get('sort_by', '')
    clear_filters = request.GET.get('clear_filters', False)

    # Handle clear filters
    if clear_filters:
        return redirect('products:product_list')

    # Apply category filter
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Apply search filter
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )

    # Apply price filter
    try:
        min_price = int(min_price)
        max_price = int(max_price)
        products = products.filter(price__gte=min_price, price__lte=max_price)
    except (ValueError, TypeError):
        min_price = 100
        max_price = 3000

    # Apply sorting
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created')

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    
    return render(request, 'products/product/list.html', context)

def product_detail(request, id, slug):
    product = get_object_or_404(
        Product,
        id=id,
        slug=slug,
        available=True
    )
    return render(request, 'products/product/detail.html', {
        'product': product
    })
