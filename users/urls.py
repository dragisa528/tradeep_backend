from django.urls import path
from .views import home, profile, OtpView, RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='users-register'),
]
