from django.shortcuts import render, redirect
from django.db.models import Q
from django.views import generic
from django.http import HttpResponse
from mydak.models import BlogPost, BlogCategory, Listing
from django.contrib import messages
from django.db import transaction
from .forms import TenantRegistrationForm
from .models import Client, ClientDomain, User

def refs(request):
    """
    Root path handler - shows the new homepage with hero and featured shops
    """
    return render(request, 'homepage.html')

def homepage_view(request):
    return render(request, 'homepage.html')

def homepage_view_x(request):
    return render(request, 'index.html')

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
    return render(request, 'product.html')

def login_view(request):
    return render(request, 'accounts/login.html')

def explore_view(request):
    """Browse all shops"""
    return render(request, 'explore.html')

def listings_view(request):
    """Browse all listings/products"""
    return render(request, 'listings.html')

def shop_detail_view(request, shop_id=None):
    """View a specific shop"""
    # Mock shop data for now
    shop_data = {
        'shop': {
            'name': f'Shop #{shop_id}' if shop_id else 'Sample Shop',
            'owner': {
                'get_full_name': 'John Seller',
                'username': 'johnseller'
            },
            'description': 'A curated collection of quality items from talented creators.',
            'rating': 4.8,
            'banner': None,
            'logo': None,
        },
        'listings_count': 24,
        'followers_count': 156,
    }
    return render(request, 'shop_detail.html', shop_data)

def listing_detail_view(request, listing_id=None):
    """View a specific product listing"""
    # Mock listing data for now
    listing_data = {
        'listing': {
            'id': listing_id or 1,
            'title': f'Premium Product #{listing_id}' if listing_id else 'Premium Electronics Item',
            'price': 4999.99,
            'original_price': 5999.99,
            'description': 'A high-quality product from a trusted seller. Perfect condition and fully functional. Comes with warranty and after-sales support.',
            'category': 'Electronics',
            'condition': 'New',
            'location': 'Nairobi, Kenya',
            'created_at': '2025-01-15T10:30:00Z',
            'image': None,
            'specs': {
                'Brand': 'Premium',
                'Model': 'PRO-2025',
                'Color': 'Black',
                'Warranty': '2 Years',
            },
            'seller': {
                'id': 1,
                'name': 'Premium Electronics Store',
                'slug': 'premium-electronics-store',
                'rating': 4.8,
                'logo': None,
            },
        },
        'reviews_count': 23,
        'seller_reviews_count': 142,
        'seller_listings_count': 47,
        'related_listings': [
            {
                'id': 2,
                'title': 'Similar Premium Product',
                'price': 3999.99,
                'original_price': None,
                'image': None,
                'rating': 4.5,
                'category': 'Electronics',
                'created_at': '2025-01-14T08:00:00Z',
                'seller': {
                    'id': 1,
                    'name': 'Premium Electronics Store',
                    'slug': 'premium-electronics-store',
                }
            }
        ],
        'site_name': 'SMW Marketplace',
    }
    return render(request, 'listing_detail.html', listing_data)

def universities_view(request):
    """Browse universities"""
    return render(request, 'universities.html')

def locations_view(request):
    """Browse locations"""
    return render(request, 'locations.html')

def create_shop_view(request):
    """Shop creation wizard"""
    if request.method == 'POST':
        # Handle shop creation
        return render(request, 'create_shop.html', {'success': True})
    return render(request, 'create_shop.html')


@transaction.atomic
def tenant_register_view(request):
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            university_name = form.cleaned_data['university_name']
            preferred_subdomain = form.cleaned_data.get('preferred_subdomain')

            subdomain = ""
            main_domain = "localhost"  # Change for production

            # Use the user's preferred subdomain if they provided a valid one
            if preferred_subdomain:
                subdomain = preferred_subdomain
            else:
                # Otherwise, auto-generate a unique subdomain from the university name
                base_slug = slugify(university_name)
                subdomain = base_slug
                while ClientDomain.objects.filter(domain=f"{subdomain}.{main_domain}").exists():
                    # Append a timestamp to ensure uniqueness if the base slug is taken
                    subdomain = f"{base_slug}-{int(time.time())}"

            # --- 1. Create the Tenant (Client) ---
            # The schema_name must be unique and URL-friendly
            schema_name = subdomain.replace('-', '_')
            tenant = Client(
                name=university_name,
                schema_name=schema_name,
                type='university',
                on_trial=True
            )
            tenant.save()

            # --- 2. Create the Tenant Domain ---
            domain_name = f"{subdomain}.{main_domain}"

            domain = ClientDomain(
                domain=domain_name,
                tenant=tenant,
                is_primary=True
            )
            domain.save()

            # --- 3. Create the University Admin User ---
            # Now using the dedicated 'username' field from the form
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                role='university_admin'
            )

            messages.success(request,
                             f"University '{university_name}' and admin account for '{user.username}' created successfully!")
            return redirect('login')

    else:
        form = TenantRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def search(request):
    query = request.GET.get('query', '')
    listings = Listing.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    )
    return render(request, 'search_results.html', {'listings': listings, 'query': query})



class BlogListView(generic.ListView):
    """
    View to display a list of all published blog posts.
    """
    model = BlogPost
    # The template name specifies which HTML file to use for rendering the list.
    template_name = 'blog/blog_list.html'
    # The context_object_name is the variable name we'll use in the template to loop through.
    context_object_name = 'posts'
    # Ensure we only fetch posts that are marked as 'Published'.
    queryset = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)
    # Number of posts per page, if you want pagination.
    paginate_by = 6

    def get_context_data(self, **kwargs):
        # Add categories to the context so we can display them in a sidebar.
        context = super().get_context_data(**kwargs)
        context['categories'] = BlogCategory.objects.all()
        return context


class BlogDetailView(generic.DetailView):
    """
    View to display a single, detailed blog post.
    """
    model = BlogPost
    # The template name specifies which HTML file to use for rendering the single post.
    template_name = 'blog/blog_detail.html'
    # The context_object_name is the variable we'll use in the template.
    context_object_name = 'post'
    # This view will automatically use the 'slug' from the URL to fetch the correct post.
    queryset = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)

    def get_context_data(self, **kwargs):
        # Add recent posts to the context for a "Recent Posts" sidebar.
        context = super().get_context_data(**kwargs)
        context['recent_posts'] = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).exclude(pk=self.object.pk).order_by('-created_on')[:5]
        context['categories'] = BlogCategory.objects.all()
        return context

