from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def home(request):
    return render(request, 'home.html')

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Subscription

@require_POST
def subscribe(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        city = data.get('city')
        
        if not email or not city:
            return JsonResponse({'status': 'error', 'message': 'Email and city are required'})
        
        Subscription.objects.get_or_create(email=email, city=city)
        return JsonResponse({'status': 'success', 'message': 'Subscribed successfully!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

import requests
from django.conf import settings

import openmeteo_requests
import requests_cache
from retry_requests import retry

def proxy_openaq(request):
    city = request.GET.get('city')
    if not city:
        return JsonResponse({'error': 'City parameter is required'}, status=400)
    
    try:
        # Setup OpenMeteo client
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)
        
        # 1. Geocode city name to get coordinates
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=5&language=en&format=json"
        geocode_response = requests.get(geocode_url)
        geocode_data = geocode_response.json()
        
        results = []
        
        if geocode_data.get('results'):
            # 2. Get air quality for each location (limit to 5)
            for location in geocode_data['results'][:5]:
                lat = location['latitude']
                lon = location['longitude']
                location_name = location['name']
                country = location.get('country', 'Unknown')
                
                # Fetch air quality data
                aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "current": ["pm10", "pm2_5", "us_aqi"]
                }
                
                try:
                    aq_responses = openmeteo.weather_api(aq_url, params=params)
                    aq_response = aq_responses[0]
                    current = aq_response.Current()
                    
                    # Extract values
                    pm25_value = current.Variables(0).Value()
                    pm10_value = current.Variables(1).Value()
                    aqi_value = current.Variables(2).Value()
                    
                    measurements = []
                    if pm25_value is not None:
                        measurements.append({
                            'parameter': 'pm25',
                            'value': round(pm25_value, 1),
                            'unit': 'µg/m³'
                        })
                    if pm10_value is not None:
                        measurements.append({
                            'parameter': 'pm10',
                            'value': round(pm10_value, 1),
                            'unit': 'µg/m³'
                        })
                    if aqi_value is not None:
                        measurements.append({
                            'parameter': 'us_aqi',
                            'value': round(aqi_value),
                            'unit': ''
                        })
                    
                    if measurements:
                        results.append({
                            'location': location_name,
                            'city': city,
                            'country': country,
                            'measurements': measurements
                        })
                except Exception:
                    continue
                    
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

