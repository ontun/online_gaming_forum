from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.home, name='home'),
    path('advertisements/', views.advertisement_list, name='advertisement_list'),
    path('advertisement/<int:pk>/', views.advertisement_detail, name='advertisement_detail'),
    path('advertisement/create/', views.advertisement_create, name='advertisement_create'),
    path('advertisement/<int:pk>/response/', views.response_create, name='response_create'),
    path('user/responses/', views.user_responses, name='user_responses'),
    path('response/<int:pk>/delete/', views.delete_response, name='delete_response'),
    path('response/<int:pk>/accept/', views.accept_response, name='accept_response'),
    path('profile/', views.profile, name='profile'),
    path('accounts/signup/', views.signup, name='account_signup'),
    path('advertisement/<int:pk>/edit/', views.advertisement_edit, name='advertisement_edit'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
