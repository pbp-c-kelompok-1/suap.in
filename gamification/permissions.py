from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsGamificationStaffOrReadOnly(BasePermission):
    message = "Only the staff can edit badges."

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
            or request.user.is_superuser
            or request.user.is_staff
        )