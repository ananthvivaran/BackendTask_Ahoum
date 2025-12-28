from rest_framework.permissions import BasePermission
from .models import Profile


class IsFacilitator(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.profile.role == 'facilitator'
        except:
            return False
