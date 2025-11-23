from django.core.management.base import BaseCommand
from core.models import Subscription
from django.core.mail import send_mail
from django.conf import settings
import time
import requests
import openmeteo_requests
import requests_cache
from retry_requests import retry

class Command(BaseCommand):
    help = 'Check air quality and send alerts'

    def handle(self, *args, **options):
        self.stdout.write('Starting alert check...')
        
        # Get all unique cities
        cities = Subscription.objects.values_list('city', flat=True).distinct()
        
        # Setup OpenMeteo client
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)
        
        for city in cities:
            self.stdout.write(f'Checking {city}...')
            try:
                # 1. Geocode city
                geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
                geocode_response = requests.get(geocode_url)
                geocode_data = geocode_response.json()
                
                if geocode_data.get('results'):
                    location = geocode_data['results'][0]
                    lat = location['latitude']
                    lon = location['longitude']
                    
                    # 2. Get air quality
                    aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
                    params = {
                        "latitude": lat,
                        "longitude": lon,
                        "current": ["pm2_5", "us_aqi"]
                    }
                    
                    aq_responses = openmeteo.weather_api(aq_url, params=params)
                    aq_response = aq_responses[0]
                    current = aq_response.Current()
                    
                    pm25_value = current.Variables(0).Value()
                    aqi_value = current.Variables(1).Value()
                    
                    if pm25_value and pm25_value > 35:  # Threshold
                        self.send_alerts(city, pm25_value, aqi_value)
                    else:
                        self.stdout.write(f'Air quality in {city} is okay (PM2.5: {pm25_value}, AQI: {aqi_value}).')
                else:
                    self.stdout.write(f'Could not geocode {city}.')
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error checking {city}: {e}'))
            
            time.sleep(1)  # Rate limiting

    def send_alerts(self, city, pm25, aqi):
        subscriptions = Subscription.objects.filter(city=city)
        emails = [sub.email for sub in subscriptions]
        
        if emails:
            subject = f'Daily Air Quality Update: {city}'
            message = f'Current Air Quality in {city}:\n\n'
            message += f'• AQI: {int(aqi)} (US AQI)\n'
            message += f'• PM2.5: {pm25} µg/m³\n\n'
            
            if aqi > 300:
                message += '🚨 Air quality is HAZARDOUS. Stay indoors and wear N95 mask if you must go out.'
            elif aqi > 200:
                message += '⚠️ Air quality is VERY UNHEALTHY. Wear a mask if going outside.'
            elif aqi > 150:
                message += 'Air quality is UNHEALTHY. Reduce outdoor activities.'
            elif aqi > 100:
                message += 'Air quality is UNHEALTHY for Sensitive Groups.'
            elif aqi > 50:
                message += 'Air quality is MODERATE. Sensitive groups should be cautious.'
            else:
                message += '✅ Air quality is GOOD. Great day to go outside!'
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                emails,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Sent alerts to {len(emails)} subscribers for {city}.'))
        else:
            self.stdout.write(f'No subscribers for {city}.')
