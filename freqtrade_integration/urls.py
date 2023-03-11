from django.urls import path
from freqtrade_integration import views

urlpatterns = [
    path('freqtrade/', views.index, name='freqtrade_index'),
]
