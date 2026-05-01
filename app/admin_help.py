"""
Admin help documentation and contextual help system.
Provides inline help tooltips, FAQ, and documentation pages.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


class HelpTopics:
    """Help topics and contextual help content."""
    
    TOPICS = {
        'user-management': {
            'title': 'User Management',
            'description': 'Manage user accounts, permissions, and access.',
            'sections': [
                {
                    'title': 'Creating Users',
                    'content': 'To create a new user, click the "Add User" button. Fill in the required fields: username, email, and password. Ensure password meets security requirements.'
                },
                {
                    'title': 'Editing Users',
                    'content': 'Click on a user from the list to view and edit their details. You can update email, name, permissions, and account status.'
                },
                {
                    'title': 'Suspending Users',
                    'content': 'To temporarily disable a user account, click the "Suspend" button. The user will not be able to log in but their data is preserved.'
                },
                {
                    'title': 'Deleting Users',
                    'content': 'To permanently delete a user account, click the "Delete" button. This action cannot be undone and all related data may also be affected.'
                },
            ]
        },
        'shop-management': {
            'title': 'Shop Management',
            'description': 'Manage shops, verify merchants, and handle shop operations.',
            'sections': [
                {
                    'title': 'Viewing Shops',
                    'content': 'View all shops in the system with their status, owner, and creation date. Click on a shop to see detailed information.'
                },
                {
                    'title': 'Activating/Deactivating Shops',
                    'content': 'Toggle shop status using the status button. Inactive shops cannot receive or process new listings.'
                },
                {
                    'title': 'Verifying Shops',
                    'content': 'Verify merchant shops to give them increased visibility and trust. Only admin can verify shops.'
                },
            ]
        },
        'listing-moderation': {
            'title': 'Listing Moderation',
            'description': 'Review, approve, and manage product listings.',
            'sections': [
                {
                    'title': 'Moderation Queue',
                    'content': 'View pending listings that require review. Each listing shows title, category, price, and shop owner.'
                },
                {
                    'title': 'Approving Listings',
                    'content': 'To approve a listing, click the "Approve" button. The listing will become visible to users.'
                },
                {
                    'title': 'Rejecting Listings',
                    'content': 'To reject a listing, click the "Reject" button and provide a reason. The seller will be notified.'
                },
                {
                    'title': 'Flagging Listings',
                    'content': 'Mark suspicious or inappropriate listings for review using the "Flag" button.'
                },
            ]
        },
        'transactions': {
            'title': 'Transaction Management',
            'description': 'Monitor and manage financial transactions.',
            'sections': [
                {
                    'title': 'Viewing Transactions',
                    'content': 'See all transactions in the system with amounts, status, and timestamps.'
                },
                {
                    'title': 'Refunding Transactions',
                    'content': 'Process refunds by clicking the "Refund" button. The refund will be returned to the buyer\'s account.'
                },
                {
                    'title': 'Disputed Transactions',
                    'content': 'Handle transaction disputes by reviewing evidence from both buyer and seller.'
                },
            ]
        },
        'roles-permissions': {
            'title': 'Roles & Permissions',
            'description': 'Understand admin roles and their permissions.',
            'sections': [
                {
                    'title': 'Superuser',
                    'content': 'Highest level of access. Can manage all resources, create other admins, and access system settings.'
                },
                {
                    'title': 'Admin',
                    'content': 'Can manage users, shops, listings, transactions, and categories. Cannot manage other admins or system settings.'
                },
                {
                    'title': 'Moderator',
                    'content': 'Can review and moderate listings, users, and handle reports. Cannot manage system settings.'
                },
                {
                    'title': 'Support',
                    'content': 'Can view information and help users. Limited to read-only access and user support functions.'
                },
                {
                    'title': 'Viewer',
                    'content': 'Can view analytics and reports. No modification permissions.'
                },
            ]
        },
        'themes': {
            'title': 'Theme Management',
            'description': 'Customize site appearance and themes.',
            'sections': [
                {
                    'title': 'Creating Themes',
                    'content': 'Create custom themes by clicking "Add Theme". Upload CSS, configure colors, and customize tokens.'
                },
                {
                    'title': 'Activating Themes',
                    'content': 'Only one theme can be active at a time. Click "Activate" to set a theme as active for all users.'
                },
                {
                    'title': 'Publishing Themes',
                    'content': 'Publish themes to make them available for users to select. Published themes appear in theme switcher.'
                },
            ]
        },
        'analytics': {
            'title': 'Analytics & Reporting',
            'description': 'View system analytics and generate reports.',
            'sections': [
                {
                    'title': 'Dashboard Metrics',
                    'content': 'Overview of key metrics: total users, active shops, pending listings, and transaction volume.'
                },
                {
                    'title': 'Generating Reports',
                    'content': 'Generate and export reports in CSV or PDF format. Filter by date range and other criteria.'
                },
                {
                    'title': 'Audit Logs',
                    'content': 'Review complete audit trail of admin actions, including who did what and when.'
                },
            ]
        },
    }
    
    @staticmethod
    def get_topic(topic_id):
        """Get help topic by ID."""
        return HelpTopics.TOPICS.get(topic_id)
    
    @staticmethod
    def get_all_topics():
        """Get all help topics."""
        return HelpTopics.TOPICS
    
    @staticmethod
    def search_topics(query):
        """Search help topics by title or content."""
        query_lower = query.lower()
        results = []
        
        for topic_id, topic in HelpTopics.TOPICS.items():
            if query_lower in topic['title'].lower() or query_lower in topic['description'].lower():
                results.append({'id': topic_id, **topic})
            else:
                # Search in sections
                matching_sections = []
                for section in topic.get('sections', []):
                    if (query_lower in section['title'].lower() or 
                        query_lower in section['content'].lower()):
                        matching_sections.append(section)
                
                if matching_sections:
                    results.append({
                        'id': topic_id,
                        'title': topic['title'],
                        'description': topic['description'],
                        'sections': matching_sections
                    })
        
        return results


class FAQ:
    """Frequently Asked Questions."""
    
    QUESTIONS = [
        {
            'question': 'How do I create an admin user?',
            'answer': 'Go to User Management > Add User. Fill in the required fields and select the appropriate admin role. The user will receive credentials and can log in immediately.'
        },
        {
            'question': 'Can I reset a user\'s password?',
            'answer': 'Yes. Go to User Management, find the user, and click "Reset Password". A temporary password will be generated and the user will be prompted to change it on next login.'
        },
        {
            'question': 'How do I moderate listings?',
            'answer': 'Go to Moderation > Pending Listings. Review each listing and approve, reject, or flag as appropriate. You can view details and seller information.'
        },
        {
            'question': 'Can I export data?',
            'answer': 'Yes. Most list pages have an "Export to CSV" button. You can also use the Analytics section to generate and export reports.'
        },
        {
            'question': 'What is the difference between roles?',
            'answer': 'Each role has different permissions. Superuser has full access, Admin can manage most resources, Moderator handles content moderation, Support assists users, and Viewer can only view reports.'
        },
        {
            'question': 'How do I change the site theme?',
            'answer': 'Go to Theme Management. Create or upload a new theme, then click "Activate" to set it as the default for all users.'
        },
        {
            'question': 'Can I see who made changes to the system?',
            'answer': 'Yes. Go to Audit Logs to see a complete history of all admin actions, including user, action type, and timestamp.'
        },
        {
            'question': 'How do I handle refunds?',
            'answer': 'Go to Transactions, find the transaction, and click "Refund". The amount will be returned to the buyer\'s account.'
        },
    ]
    
    @staticmethod
    def get_all():
        """Get all FAQ entries."""
        return FAQ.QUESTIONS
    
    @staticmethod
    def search(query):
        """Search FAQ by question or answer."""
        query_lower = query.lower()
        return [
            faq for faq in FAQ.QUESTIONS
            if query_lower in faq['question'].lower() or query_lower in faq['answer'].lower()
        ]


class Glossary:
    """Admin glossary of terms."""
    
    TERMS = {
        'listing': 'A product or service offered for sale on the marketplace.',
        'shop': 'A seller\'s storefront where they list and manage their products.',
        'moderation': 'The process of reviewing and approving content before it\'s published.',
        'suspension': 'Temporarily disabling an account while preserving its data.',
        'role': 'An admin level that determines what actions can be performed.',
        'permission': 'A specific action or resource access that a role allows.',
        'transaction': 'A financial exchange between a buyer and seller.',
        'refund': 'Returning money to a buyer for a transaction.',
        'audit log': 'A complete record of all admin actions and system changes.',
        'theme': 'The visual design and styling of the platform.',
    }
    
    @staticmethod
    def get_term(term):
        """Get term definition."""
        return Glossary.TERMS.get(term.lower())
    
    @staticmethod
    def get_all():
        """Get all glossary terms."""
        return Glossary.TERMS


# View functions for help pages

@require_http_methods(["GET"])
def help_index(request):
    """Help documentation index page."""
    from django.shortcuts import render
    
    topics = HelpTopics.get_all_topics()
    faq = FAQ.get_all()
    
    context = {
        'topics': topics,
        'faq': faq,
        'title': 'Help & Documentation',
    }
    
    return render(request, 'admin/help/index.html', context)


@require_http_methods(["GET"])
def help_topic(request, topic_id):
    """Help topic detail page."""
    from django.shortcuts import render, get_object_or_404
    
    topic = HelpTopics.get_topic(topic_id)
    if not topic:
        get_object_or_404(dict, pk=topic_id)  # Raise 404
    
    context = {
        'topic': topic,
        'title': f'Help: {topic["title"]}',
    }
    
    return render(request, 'admin/help/topic.html', context)


@require_http_methods(["GET"])
def help_search(request):
    """Search help documentation."""
    query = request.GET.get('q', '').strip()
    
    results = {
        'topics': [],
        'faq': [],
    }
    
    if query:
        results['topics'] = HelpTopics.search_topics(query)
        results['faq'] = FAQ.search(query)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(results)
    
    from django.shortcuts import render
    context = {
        'query': query,
        'results': results,
        'title': f'Help Search: {query}' if query else 'Help Search',
    }
    
    return render(request, 'admin/help/search.html', context)
