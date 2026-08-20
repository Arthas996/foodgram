import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import CustomPagination

from .models import Subscription, User
from .serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny]
        elif self.action in ('me', 'avatar', 'subscribe', 'subscriptions'):
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'avatar': 'Это поле обязательно.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                format, imgstr = avatar_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'avatar_{user.id}.{ext}',
                )
                user.avatar.save(data.name, data, save=True)
            except Exception:
                return Response(
                    {'avatar': 'Неверный формат изображения'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {'avatar': request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK,
            )
        # DELETE
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            sub, created = Subscription.objects.get_or_create(
                user=user,
                author=author,
            )
            if not created:
                return Response(
                    {'error': 'Уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = UserWithRecipesSerializer(
                author,
                context={'request': request},
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        sub = Subscription.objects.filter(user=user, author=author)
        if not sub.exists():
            return Response(
                {'error': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sub.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)

        page = self.paginate_queryset(subscriptions)
        if page is not None:
            authors = [sub.author for sub in page]
            serializer = UserWithRecipesSerializer(
                authors,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)

        authors = [sub.author for sub in subscriptions]
        serializer = UserWithRecipesSerializer(
            authors,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)


class AvatarView(APIView):
    """Отдельное представление для работы с аватаром"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        avatar_data = request.data.get('avatar')
        if not avatar_data:
            return Response(
                {'avatar': 'Это поле обязательно.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            format, imgstr = avatar_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'avatar_{user.id}.{ext}',
            )
            user.avatar.save(data.name, data, save=True)
        except Exception:
            return Response(
                {'avatar': 'Неверный формат изображения'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'avatar': request.build_absolute_uri(user.avatar.url)},
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
