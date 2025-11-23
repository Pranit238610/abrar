from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User
from core.models import Subscription
import json

class Command(BaseCommand):
    help = 'Verifies the system endpoints and flows'

    def handle(self, *args, **options):
        self.stdout.write('Starting verification...')
        client = Client(enforce_csrf_checks=True)

        # 1. Test Home Page
        response = client.get('/')
        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS('Home page: OK'))
            self.stdout.write(f"Home response cookies: {response.cookies}")
        else:
            self.stdout.write(self.style.ERROR(f'Home page failed: {response.status_code}'))

        # 2. Test OpenAQ Proxy
        self.stdout.write('Testing OpenAQ Proxy...')
        response = client.get('/proxy/openaq/?city=London')
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                self.stdout.write(self.style.SUCCESS('OpenAQ Proxy: OK'))
            else:
                self.stdout.write(self.style.WARNING('OpenAQ Proxy: Response format unexpected'))
        else:
            self.stdout.write(self.style.ERROR(f'OpenAQ Proxy failed: {response.status_code}'))

        # 3. Test Subscription (Requires Login)
        self.stdout.write('Testing Subscription...')
        username = 'testuser_verify'
        password = 'password123'
        email = 'test@example.com'
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, email=email, password=password)
        
        login_success = client.login(username=username, password=password)
        if login_success:
            self.stdout.write(self.style.SUCCESS('Login: OK'))
            
            # Get CSRF token
            self.stdout.write(f"Cookies: {client.cookies.keys()}")
            if 'csrftoken' in client.cookies:
                csrftoken = client.cookies['csrftoken'].value
            else:
                csrftoken = ''
                self.stdout.write(self.style.WARNING("CSRF token missing in cookies"))
            
            # Try to subscribe
            response = client.post(
                '/subscribe/',
                json.dumps({'city': 'London'}),
                content_type='application/json',
                HTTP_X_CSRFTOKEN=csrftoken
            )
            
            if response.status_code == 200 and response.json().get('status') == 'success':
                if Subscription.objects.filter(user__username=username, city='London').exists():
                    self.stdout.write(self.style.SUCCESS('Subscription: OK'))
                else:
                    self.stdout.write(self.style.ERROR('Subscription: DB record missing'))
            else:
                with open('subscription_error.html', 'wb') as f:
                    f.write(response.content)
                self.stdout.write(self.style.ERROR(f'Subscription failed: {response.status_code}. See subscription_error.html'))
        else:
            self.stdout.write(self.style.ERROR('Login failed'))

        # Cleanup
        User.objects.filter(username=username).delete()
