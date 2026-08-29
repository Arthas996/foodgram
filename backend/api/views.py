import base64

from django.core.files.base import ContentFile
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import RecipeFilter
from api.pagination import Pagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class AvatarView(APIView):
    """Представление для добавления и удаления аватара."""

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


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов с поиском по имени."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    ]
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_to_related(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        try:
            obj, created = model.objects.get_or_create(user=user, recipe=recipe)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not created:
            return Response(
                {'error': 'Уже добавлено'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            RecipeShortSerializer(recipe, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    def _remove_from_related(self, model, request, pk):
        user = request.user
        try:
            deleted, _ = model.objects.filter(user=user, recipe__id=pk).delete()
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if deleted == 0:
            return Response(
                {'error': 'Не найдено'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self._add_to_related(Favorite, request, pk)
        return self._remove_from_related(Favorite, request, pk)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self._add_to_related(ShoppingCart, request, pk)
        return self._remove_from_related(ShoppingCart, request, pk)

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        base_url = request.build_absolute_uri('/')[:-1]
        short_link = f'{base_url}/s/{recipe.id}'
        return Response({'short-link': short_link})

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        user = request.user
        cart_items = ShoppingCart.objects.filter(user=user)
        recipes = [item.recipe for item in cart_items]
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )
        content = self._prepare_shopping_list_text(ingredients)
        return self._create_file_response(content)

    def _prepare_shopping_list_text(self, ingredients):
        lines = [
            f"{ing['ingredient__name']} "
            f"({ing['ingredient__measurement_unit']}) — {ing['total']}"
            for ing in ingredients
        ]
        return '\n'.join(lines)

    def _create_file_response(self, content):
        return FileResponse(
            content,
            content_type='text/plain',
            filename='shopping_list.txt',
        )


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Вьюсет для пользователей (регистрация, профиль, подписки)."""

    queryset = User.objects.all()
    serializer_class = UserWithRecipesSerializer
    pagination_class = Pagination

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        if self.action == 'create':
            return UserCreateSerializer
        # Для list, retrieve, me используем базовый сериализатор
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
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

        deleted, _ = Subscription.objects.filter(
            user=user,
            author=author,
        ).delete()
        if deleted == 0:
            return Response(
                {'error': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(following__user=user).distinct()
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserWithRecipesSerializer(
            authors,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)
