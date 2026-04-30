"""Integration and E2E tests for UniMarket."""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from app.models import Client as TenantClient
from mydak.models import Shop, Listing, Category, Transaction, Conversation, Message

User = get_user_model()


class UserAuthTests(TestCase):
    """Tests for user authentication and registration."""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:signup')
        self.login_url = reverse('accounts:login')
    
    def test_user_registration(self):
        """Test user can register."""
        response = self.client.post(self.register_url, {
            'email': 'test@example.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        }, follow=True)
        
        # User should be created
        user = User.objects.filter(email='test@example.com').first()
        self.assertIsNotNone(user)
    
    def test_user_login(self):
        """Test user can login."""
        # Create user
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!'
        )
        user.is_active = True
        user.save()
        
        # Login
        response = self.client.post(self.login_url, {
            'login': 'test@example.com',
            'password': 'TestPassword123!',
        }, follow=True)
        
        # Check login was successful
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class ShopWorkflowTests(TestCase):
    """End-to-end tests for shop creation and management."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='seller@example.com',
            password='TestPassword123!',
            role='seller'
        )
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_complete_shop_setup(self):
        """Test complete workflow: create shop, create listing."""
        # Create shop
        shop = Shop.objects.create(
            name='My Electronics Shop',
            owner=self.user,
            description='Electronics and gadgets',
            is_active=True
        )
        
        # Create category
        category = Category.objects.create(name='Laptops')
        
        # Create listing
        listing = Listing.objects.create(
            title='MacBook Pro 16"',
            description='Used MacBook Pro in excellent condition',
            price=120000,
            seller=self.user,
            shop=shop,
            category=category,
            condition='good',
            status='draft'
        )
        
        # Publish listing
        listing.status = 'active'
        listing.save()
        
        # Verify workflow
        self.assertEqual(shop.owner, self.user)
        self.assertEqual(listing.seller, self.user)
        self.assertEqual(listing.status, 'active')
        self.assertEqual(listing.shop, shop)


class BuyerSellerInteractionTests(TestCase):
    """Tests for buyer-seller interactions."""
    
    def setUp(self):
        self.buyer = User.objects.create_user(
            email='buyer@example.com',
            password='TestPassword123!',
            role='buyer'
        )
        
        self.seller = User.objects.create_user(
            email='seller@example.com',
            password='TestPassword123!',
            role='seller'
        )
        
        self.shop = Shop.objects.create(
            name='Test Shop',
            owner=self.seller,
            is_active=True
        )
        
        self.category = Category.objects.create(name='Electronics')
        
        self.listing = Listing.objects.create(
            title='Test Laptop',
            description='A test laptop',
            price=50000,
            seller=self.seller,
            shop=self.shop,
            category=self.category,
            status='active'
        )
    
    def test_buyer_initiates_conversation(self):
        """Test buyer can start conversation about listing."""
        conversation = Conversation.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            listing=self.listing
        )
        
        # Buyer sends message
        message = Message.objects.create(
            conversation=conversation,
            sender=self.buyer,
            receiver=self.seller,
            listing=self.listing,
            content='Is this still available? Can you ship to Nairobi?'
        )
        
        # Seller responds
        response = Message.objects.create(
            conversation=conversation,
            sender=self.seller,
            receiver=self.buyer,
            listing=self.listing,
            content='Yes, still available. Shipping available nationwide.'
        )
        
        # Verify conversation
        messages = conversation.messages.all().order_by('created_at')
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages.first().sender, self.buyer)
        self.assertEqual(messages.last().sender, self.seller)


class PaymentWorkflowTests(TestCase):
    """Tests for payment and transaction workflows."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='TestPassword123!'
        )
    
    def test_listing_post_payment_flow(self):
        """Test workflow for posting a listing (includes payment)."""
        # Create transaction for listing post
        transaction = Transaction.objects.create(
            user=self.user,
            action='listing_post',
            amount=50,
            status='pending',
            payment_method='mpesa'
        )
        
        # Initiate payment
        transaction.mark_as_initiated()
        self.assertEqual(transaction.status, 'initiated')
        
        # Payment success
        transaction.mark_as_success()
        self.assertEqual(transaction.status, 'success')
        
        # Verify listing post is available
        self.assertEqual(transaction.action, 'listing_post')
    
    def test_shop_creation_payment_flow(self):
        """Test workflow for creating a shop (includes payment)."""
        # Create transaction for shop creation
        transaction = Transaction.objects.create(
            user=self.user,
            action='shop_creation',
            amount=500,
            status='pending',
            payment_method='mpesa',
            phone_number='254712345678'
        )
        
        # Simulate payment success
        transaction.mpesa_receipt = 'EEV6WE2ER'
        transaction.mark_as_success()
        
        # Verify payment
        self.assertEqual(transaction.status, 'success')
        self.assertIsNotNone(transaction.mpesa_receipt)


class ListingSearchTests(TestCase):
    """Tests for listing search and filtering."""
    
    def setUp(self):
        self.seller = User.objects.create_user(
            email='seller@example.com',
            password='TestPassword123!',
            role='seller'
        )
        
        self.shop = Shop.objects.create(
            name='Test Shop',
            owner=self.seller,
            is_active=True
        )
        
        self.electronics = Category.objects.create(name='Electronics')
        self.books = Category.objects.create(name='Books')
        
        # Create test listings
        Listing.objects.create(
            title='MacBook Pro 16"',
            description='Used laptop',
            price=120000,
            seller=self.seller,
            shop=self.shop,
            category=self.electronics,
            condition='good',
            status='active',
            views=10
        )
        
        Listing.objects.create(
            title='iPhone 13',
            description='Used phone',
            price=45000,
            seller=self.seller,
            shop=self.shop,
            category=self.electronics,
            condition='excellent',
            status='active',
            views=5
        )
        
        Listing.objects.create(
            title='Django for Beginners',
            description='Programming book',
            price=800,
            seller=self.seller,
            shop=self.shop,
            category=self.books,
            condition='new',
            status='active',
            views=2
        )
    
    def test_search_by_title(self):
        """Test search by listing title."""
        results = Listing.objects.filter(
            title__icontains='MacBook',
            status='active'
        )
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().title, 'MacBook Pro 16"')
    
    def test_filter_by_category(self):
        """Test filter by category."""
        results = Listing.objects.filter(
            category=self.electronics,
            status='active'
        )
        self.assertEqual(results.count(), 2)
    
    def test_filter_by_price_range(self):
        """Test filter by price range."""
        results = Listing.objects.filter(
            price__gte=10000,
            price__lte=50000,
            status='active'
        )
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().title, 'iPhone 13')
    
    def test_filter_by_condition(self):
        """Test filter by condition."""
        results = Listing.objects.filter(
            condition='excellent',
            status='active'
        )
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().title, 'iPhone 13')
    
    def test_sort_by_price(self):
        """Test sort by price."""
        results = Listing.objects.filter(
            status='active'
        ).order_by('-price')
        
        prices = [l.price for l in results]
        self.assertEqual(prices, sorted(prices, reverse=True))
    
    def test_sort_by_popularity(self):
        """Test sort by views (popularity)."""
        results = Listing.objects.filter(
            status='active'
        ).order_by('-views')
        
        views = [l.views for l in results]
        self.assertEqual(views, sorted(views, reverse=True))


class AdminDashboardTests(TestCase):
    """Tests for admin dashboard functionality."""
    
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@university.edu',
            password='TestPassword123!',
            role='university_admin'
        )
        
        # Create shops under admin's university
        for i in range(5):
            seller = User.objects.create_user(
                email=f'seller{i}@example.com',
                password='TestPassword123!',
                role='seller'
            )
            
            shop = Shop.objects.create(
                name=f'Shop {i}',
                owner=seller,
                is_active=True
            )
    
    def test_admin_dashboard_stats(self):
        """Test admin can view dashboard stats."""
        shops = Shop.objects.filter(is_active=True)
        self.assertEqual(shops.count(), 5)


class DataIntegrityTests(TestCase):
    """Tests for data integrity and constraints."""
    
    def setUp(self):
        self.seller = User.objects.create_user(
            email='seller@example.com',
            password='TestPassword123!',
            role='seller'
        )
        
        self.shop = Shop.objects.create(
            name='Test Shop',
            owner=self.seller,
            is_active=True
        )
        
        self.category = Category.objects.create(name='Electronics')
    
    def test_listing_seller_integrity(self):
        """Test listing seller relationship integrity."""
        listing = Listing.objects.create(
            title='Test Item',
            description='Test',
            price=5000,
            seller=self.seller,
            shop=self.shop,
            category=self.category,
            status='active'
        )
        
        # Verify seller is set
        self.assertEqual(listing.seller, self.seller)
        self.assertIsNotNone(listing.created_at)
        self.assertIsNotNone(listing.updated_at)
    
    def test_shop_category_relationship(self):
        """Test shop and category relationships."""
        listing = Listing.objects.create(
            title='Test Item',
            description='Test',
            price=5000,
            seller=self.seller,
            shop=self.shop,
            category=self.category,
            status='active'
        )
        
        # Verify relationships
        self.assertEqual(listing.shop, self.shop)
        self.assertEqual(listing.category, self.category)
        self.assertIn(listing, self.shop.listings.all())
