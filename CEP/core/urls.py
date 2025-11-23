from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('proxy/openaq/', views.proxy_openaq, name='proxy_openaq'),
]
