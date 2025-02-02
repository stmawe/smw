from django.shortcuts import render

def refs(request):
    return render(request, 'ref.html')

def homepage_view(request):
    return render(request, 'homepage.html')

def about_view(request):
    return render(request, 'about.html')

def features_view(request):
    return render(request, 'features.html')

def blog_view(request):
    return render(request, 'blog.html')

def faq_view(request):
    return render(request, 'faq.html')

def contact_view(request):
    return render(request, 'contact.html')

def products_view(request):
    return render(request, 'products.html')

def login_view(request):
    return render(request, 'login.html')

def register_view(request):
    return render(request, 'register.html')