from django.urls import path
from .views import (
    signup, verify_email,
    list_events, create_event,
    update_event, delete_event, event_detail,
    CustomTokenView
)
from .views import my_events

urlpatterns = [
    # 🔐 Auth
    path('auth/signup/', signup),
    path('auth/verify-email/', verify_email),
    path('auth/login/', CustomTokenView.as_view(), name='token_obtain_pair'),
    path('events/mine/', my_events),


    # 🎯 Events
    path('events/', list_events),
    path('events/create/', create_event),
    path('events/<int:pk>/', event_detail),
    path('events/<int:pk>/update/', update_event),
    path('events/<int:pk>/delete/', delete_event),
]
