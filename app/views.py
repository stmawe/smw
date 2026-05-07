import time

from django.shortcuts import render, redirect
from django.db.models import Q
from django.views import generic
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from mydak.models import BlogPost, BlogCategory, Listing, Shop
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login
from .forms import TenantRegistrationForm
from .models import Client, ClientDomain, User
from datetime import datetime, timedelta
from app.shop_urls import generate_shop_slug, validate_shop_slug
from app.shop_creation_service import ShopCreationService


def _get_all_listings(limit=48):
    """
    Collect active listings from all tenant schemas.
    Returns a list of dicts with listing data + owner/shop context.
    Falls back to empty list if cross-schema query fails.
    """
    from django_tenants.utils import schema_context
    from app.models import Client, ClientDomain

    all_listings = []

    # Get all non-public tenant schemas
    tenants = Client.objects.exclude(schema_name='public').order_by('created_at')

    for tenant in tenants:
        try:
            with schema_context(tenant.schema_name):
                listings = Listing.objects.filter(
                    status='active'
                ).select_related('seller', 'shop', 'category').order_by('-created_at')[:20]

                # Find the owner's username from ClientDomain
                domain_record = ClientDomain.objects.filter(
                    tenant=tenant, is_primary=True
                ).first()
                owner_username = ''
                if domain_record:
                    from django.conf import settings as _s
                    base = getattr(_s, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
                    host = domain_record.domain
                    if host.endswith(f'.{base}'):
                        owner_username = host[: -(len(base) + 1)]

                for listing in listings:
                    shop_url = ''
                    if listing.shop:
                        if listing.shop.is_root_shop:
                            shop_url = f'https://{owner_username}.smw.pgwiz.cloud/'
                        else:
                            shop_url = f'https://{owner_username}.smw.pgwiz.cloud/{listing.shop.domain}/'

                    all_listings.append({
                        'id': listing.id,
                        'title': listing.title,
                        'price': listing.price,
                        'description': listing.description[:120] if listing.description else '',
                        'category': listing.category.name if listing.category else '',
                        'condition': listing.get_condition_display() if hasattr(listing, 'get_condition_display') else '',
                        'image': listing.image.url if listing.image else None,
                        'shop_name': listing.shop.name if listing.shop else '',
                        'shop_url': shop_url,
                        'owner_username': owner_username,
                        'created_at': listing.created_at,
                        'schema': tenant.schema_name,
                    })
        except Exception:
            continue  # Skip schemas that fail — non-fatal

    # Sort by created_at descending, cap at limit
    all_listings.sort(key=lambda x: x.get('created_at') or '', reverse=True)
    return all_listings[:limit]


def refs(request):
    """Root path — combined marketplace homepage."""
    return homepage_view(request)


def homepage_view(request):
    """
    Combined marketplace — shows active listings from all tenant schemas.
    Falls back to showing active shops if no listings exist.
    """
    listings = _get_all_listings(limit=48)

    # Fallback: get active shops from public schema for display
    active_shops = Shop.objects.filter(is_active=True).order_by('-created_at')[:12]

    return render(request, 'homepage.html', {
        'listings': listings,
        'active_shops': active_shops,
        'has_listings': bool(listings),
    })

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
    """Handle user login with username or email"""
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate using the custom backend
        user = authenticate(request, username=username_or_email, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect to dashboard or explore page
            return redirect('explore')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
    return render(request, 'accounts/login.html')

def explore_view(request):
    """Browse all shops"""
    return render(request, 'explore.html')


def shop_profile_view(request, username):
    """
    smw.pgwiz.cloud/shop/{username}/ — public profile for a user on the main site.
    Shows all their active shops and recent listings.
    """
    from django.conf import settings as _s
    from django_tenants.utils import schema_context
    from app.models import ClientDomain

    try:
        profile_user = User.objects.get(username=username)
    except User.DoesNotExist:
        from django.http import Http404
        raise Http404(f'No user found with username "{username}"')

    base_domain = getattr(_s, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
    protocol = 'http' if _s.DEBUG else 'https'
    subdomain_url = f'{protocol}://{username}.{base_domain}/'

    # Find the user's tenant schema
    domain_record = ClientDomain.objects.filter(
        domain=f'{username}.{base_domain}'
    ).select_related('tenant').first()

    shops = []
    recent_listings = []

    if domain_record:
        try:
            with schema_context(domain_record.tenant.schema_name):
                from mydak.models import Shop as TenantShop, Listing as TenantListing
                shops = list(
                    TenantShop.objects.filter(
                        owner=profile_user, is_active=True
                    ).order_by('name').values('id', 'name', 'domain', 'description', 'is_root_shop')
                )
                recent_listings = list(
                    TenantListing.objects.filter(
                        status='active'
                    ).select_related('shop', 'category').order_by('-created_at')[:12]
                )
        except Exception:
            pass

    return render(request, 'shop_profile.html', {
        'profile_user': profile_user,
        'subdomain_url': subdomain_url,
        'shops': shops,
        'recent_listings': recent_listings,
        'base_domain': base_domain,
        'protocol': protocol,
    })

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
    # Mock listing data for now - use proper datetime objects for timesince filter
    created_date = datetime.now() - timedelta(days=3)
    related_created = datetime.now() - timedelta(days=4)
    
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
            'created_at': created_date,
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
                'created_at': related_created,
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


def _wizard_catalog_data():
    from mydak.models import Category as MarketplaceCategory
    from .models import Entity

    categories = list(
        MarketplaceCategory.objects.order_by('name').values('id', 'name')
    )
    if not categories:
        categories = [
            {'id': 1, 'name': 'Electronics'},
            {'id': 2, 'name': 'Books'},
            {'id': 3, 'name': 'Fashion'},
            {'id': 4, 'name': 'Food'},
            {'id': 5, 'name': 'Services'},
            {'id': 6, 'name': 'Other'},
        ]

    # Read universities and locations from Entity DB (replaces Client tenant_type query)
    universities = list(
        Entity.objects.filter(is_active=True, entity_type='University')
        .order_by('name').values('id', 'name')
    )
    locations = list(
        Entity.objects.filter(is_active=True, entity_type='Location')
        .order_by('name').values('id', 'name')
    )

    themes = [
        {
            'id': 'dark_noir',
            'name': 'Dark Noir',
            'description': 'Sleek · Professional',
            'bg': '#120F1E',
            'surface': '#1E1530',
            'accent': '#E8B030',
            'text': '#F2EFF8',
        },
        {
            'id': 'campus_light',
            'name': 'Campus Light',
            'description': 'Fresh · Academic',
            'bg': '#F8FAFF',
            'surface': '#FFFFFF',
            'accent': '#1A72E8',
            'text': '#0A1628',
        },
        {
            'id': 'sunset_market',
            'name': 'Sunset Market',
            'description': 'Warm · Vibrant',
            'bg': '#1A0E05',
            'surface': '#2A1A0A',
            'accent': '#E8721A',
            'text': '#F5E8D8',
        },
        {
            'id': 'forest_minimal',
            'name': 'Forest Minimal',
            'description': 'Earthy · Calm',
            'bg': '#061208',
            'surface': '#0D2415',
            'accent': '#26B857',
            'text': '#E8F5EC',
        },
        {
            'id': 'neon_pulse',
            'name': 'Neon Pulse',
            'description': 'Bold · Electric',
            'bg': '#020810',
            'surface': '#080F20',
            'accent': '#00F5CC',
            'text': '#E0F8FF',
        },
    ]

    return {
        'categories': categories,
        'universities': universities,
        'locations': locations,
        'themes': themes,
        'wizard_steps': [
            {'number': 1, 'label': 'Identity'},
            {'number': 2, 'label': 'Affiliation'},
            {'number': 3, 'label': 'Design'},
            {'number': 4, 'label': 'Branding'},
            {'number': 5, 'label': 'Details'},
            {'number': 6, 'label': 'Launch'},
        ],
        'week_days': [
            {'key': 'mon', 'label': 'Mon'},
            {'key': 'tue', 'label': 'Tue'},
            {'key': 'wed', 'label': 'Wed'},
            {'key': 'thu', 'label': 'Thu'},
            {'key': 'fri', 'label': 'Fri'},
            {'key': 'sat', 'label': 'Sat'},
            {'key': 'sun', 'label': 'Sun'},
        ],
        'accent_colors': [
            {'id': 'electric-blue', 'name': 'Electric Blue', 'value': '#1A72E8'},
            {'id': 'champagne-gold', 'name': 'Champagne Gold', 'value': '#E8B030'},
            {'id': 'emerald', 'name': 'Emerald', 'value': '#26B857'},
            {'id': 'coral-red', 'name': 'Coral Red', 'value': '#F15A59'},
            {'id': 'violet', 'name': 'Violet', 'value': '#8B5CF6'},
            {'id': 'slate', 'name': 'Slate', 'value': '#64748B'},
        ],
        'banner_presets': [
            {'id': 'navy-gradient', 'name': 'Navy'},
            {'id': 'gold-glow', 'name': 'Gold Glow'},
            {'id': 'green-forest', 'name': 'Forest'},
            {'id': 'mosaic', 'name': 'Mosaic'},
        ],
        'mpesa_fee': 500,
    }


def _unique_shop_domain(shop_name):
    base_slug = generate_shop_slug(shop_name)
    if not base_slug:
        return ''

    candidate = base_slug
    suffix = 2
    while Shop.objects.filter(domain__iexact=candidate).exists():
        candidate = f'{base_slug}-{suffix}'
        suffix += 1
    return candidate

def create_shop_view(request):
    """Shop creation wizard with multi-step form and incomplete shop caching"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.info(request, 'Please log in or create an account to create a shop. You can save your progress for up to 72 hours.')
        return redirect('login')
    
    from app.shop_cache import get_incomplete_shop, cache_incomplete_shop, get_shop_progress
    from app.shop_urls import generate_shop_slug, validate_shop_slug, get_user_tier, get_user_shop_limit

    # Enforce shop limit based on user tier
    shop_count = Shop.objects.filter(owner=request.user).count()
    shop_limit = get_user_shop_limit(request.user)
    user_tier = get_user_tier(request.user)

    if shop_count >= shop_limit:
        if user_tier == 1:
            messages.error(
                request,
                'Your shop is set as your root shop (Tier 1). '
                'You can only have 1 shop at this tier. '
                'Demote your root shop or request a Tier upgrade to add more.'
            )
        else:
            messages.error(
                request,
                f'You have reached the maximum number of shops ({shop_limit}). '
                'Delete an existing shop to create a new one.'
            )
        from django.conf import settings as _s
        base = getattr(_s, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
        protocol = 'http' if _s.DEBUG else 'https'
        return redirect(f'{protocol}://{request.user.username}.{base}/dashboard/')

    # Tier 1 check: if user has a root-promoted shop, they can't create another
    has_root_shop = Shop.objects.filter(owner=request.user, is_root_shop=True, is_active=True).exists()
    if has_root_shop:
        messages.error(
            request,
            'Your shop is set as your root shop (Tier 1). '
            'To create a second shop, first demote your root shop or request a Tier upgrade.'
        )
        from django.conf import settings as _s
        base = getattr(_s, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
        protocol = 'http' if _s.DEBUG else 'https'
        return redirect(f'{protocol}://{request.user.username}.{base}/dashboard/')
    
    # Try to load incomplete shop data if user has one cached
    incomplete_shop = get_incomplete_shop(request.user.id)
    shop_progress = get_shop_progress(request.user.id)
    wizard_config = _wizard_catalog_data()
    
    if request.method == 'POST':
        payload = ShopCreationService.build_payload(request.POST)
        terms_agreed = request.POST.get('terms')
        errors = []

        if not terms_agreed:
            errors.append('You must agree to the terms and conditions.')

        slug_result = validate_shop_slug(payload['slug'])
        if not slug_result['valid'] or not slug_result['available']:
            errors.append(slug_result['error'] or 'That shop slug is not available.')

        if errors:
            for error in errors:
                messages.error(request, error)

            incomplete_data = {**payload, 'terms': bool(terms_agreed)}
            cache_incomplete_shop(request.user.id, incomplete_data)

            context = {
                'remaining_shops': 2 - shop_count,
                'shop_count': shop_count,
                'form_data': request.POST,
                'incomplete_shop': incomplete_data,
                'generated_slug': payload['slug'],
                'wizard_active_step': 6,
                'payment_state': 'failed',
            }
            context.update(wizard_config)
            return render(request, 'wizard/create_shop.html', context)

        try:
            shop, transaction_obj, payment_result = ShopCreationService.launch_shop(
                request.user,
                payload,
                request.FILES,
            )
        except ValidationError as exc:
            error_messages = exc.message_dict if hasattr(exc, 'message_dict') else {'__all__': exc.messages}
            for field_errors in error_messages.values():
                for error in field_errors:
                    messages.error(request, error)

            incomplete_data = {**payload, 'terms': bool(terms_agreed)}
            cache_incomplete_shop(request.user.id, incomplete_data)

            context = {
                'remaining_shops': 2 - shop_count,
                'shop_count': shop_count,
                'form_data': request.POST,
                'incomplete_shop': incomplete_data,
                'generated_slug': payload['slug'],
                'wizard_active_step': 6,
                'payment_state': 'failed',
            }
            context.update(wizard_config)
            return render(request, 'wizard/create_shop.html', context, status=400)
        except Exception as e:
            messages.error(request, f'Error launching shop payment: {str(e)}')

            incomplete_data = {**payload, 'terms': bool(terms_agreed)}
            cache_incomplete_shop(request.user.id, incomplete_data)

            context = {
                'remaining_shops': 2 - shop_count,
                'shop_count': shop_count,
                'form_data': request.POST,
                'incomplete_shop': incomplete_data,
                'generated_slug': payload['slug'],
                'wizard_active_step': 6,
                'payment_state': 'failed',
            }
            context.update(wizard_config)
            return render(request, 'wizard/create_shop.html', context, status=500)

        messages.info(request, 'Check your phone for the M-Pesa prompt to finish launching your shop.')
        incomplete_data = {**payload, 'terms': bool(terms_agreed)}
        cache_incomplete_shop(request.user.id, incomplete_data)
        context = {
            'remaining_shops': 2 - shop_count,
            'shop_count': shop_count,
            'form_data': request.POST,
            'incomplete_shop': incomplete_data,
            'generated_slug': shop.slug,
            'wizard_active_step': 6,
            'payment_state': 'waiting',
            'payment_phone': payload['payment_phone'],
            'payment_checkout_request_id': transaction_obj.mpesa_checkout_request_id,
            'payment_transaction_id': transaction_obj.id,
            'launch_shop': shop,
            'launch_transaction': transaction_obj,
        }
        context.update(wizard_config)
        return render(request, 'wizard/create_shop.html', context)
    
    context = {
        'remaining_shops': shop_limit - shop_count,
        'shop_count': shop_count,
        'shop_limit': shop_limit,
        'user_tier': user_tier,
        'incomplete_shop': incomplete_shop or {},
        'shop_progress': shop_progress,
        'generated_slug': generate_shop_slug((incomplete_shop or {}).get('shop_name', '')) if incomplete_shop else '',
        'wizard_config': wizard_config,
        'user_username': request.user.username,
        # Ensure all template variables have safe defaults on GET
        'form_data': {},
        'payment_phone': '',
        'payment_state': 'idle',
        'payment_checkout_request_id': '',
        'wizard_active_step': 1,
    }
    context.update(wizard_config)
    return render(request, 'wizard/create_shop.html', context)


def tenant_register_view(request):
    """
    Legacy university registration endpoint — now redirects to the standard
    user registration flow. Universities/entities are managed via the admin
    panel at admin.smw.pgwiz.cloud/admin/entities/, not via self-registration.
    """
    return redirect('accounts:register')


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
