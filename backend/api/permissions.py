from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Разрешает редактирование/удаление только автору объекта."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in ('GET', 'HEAD', 'OPTIONS')
            or obj.author == request.user
        )
