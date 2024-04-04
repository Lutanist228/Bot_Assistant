from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.RegistrationForm.as_view(), name='registration'),
]