from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('homepage.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/registration/', include('accounts.urls')),
    path('admin/', admin.site.urls),
]
