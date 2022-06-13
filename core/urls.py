from django.urls import path, include
from .views import RegisterAPIView, LoginAPIView


urlpatterns = [
    path('register', RegisterAPIView.as_view()),
    path('login', LoginAPIView.as_view()),
]
