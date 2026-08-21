from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from api.pagination import Pagination
from api.serializers import UserWithRecipesSerializer
from users.models import Subscription


class UserViewSet(DjoserUserViewSet):
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=400
                )
            sub, created = Subscription.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {'error': 'Уже подписаны'},
                    status=400
                )
            serializer = UserWithRecipesSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=201)
        # DELETE
        deleted, _ = Subscription.objects.filter(
            user=user, author=author
        ).delete()
        if deleted == 0:
            return Response(
                {'error': 'Вы не подписаны'},
                status=400
            )
        return Response(status=204)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            authors = [sub.author for sub in page]
            serializer = UserWithRecipesSerializer(
                authors, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        authors = [sub.author for sub in subscriptions]
        serializer = UserWithRecipesSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data)
