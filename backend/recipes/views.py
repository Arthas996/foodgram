from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.pagination import Pagination
from api.serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
)
from recipes.filters import RecipeFilter
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
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
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
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
        obj, created = model.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            return Response(
                {'error': 'Уже добавлено'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            RecipeShortSerializer(recipe, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def _remove_from_related(self, model, request, pk):
        user = request.user
        deleted, _ = model.objects.filter(user=user, recipe__id=pk).delete()
        if deleted == 0:
            return Response(
                {'error': 'Не найдено'},
                status=status.HTTP_400_BAD_REQUEST
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
        short_link = f"{request.build_absolute_uri('/')[:-1]}/s/{recipe.id}"
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
        )

        lines = [
            f"{ing['ingredient__name']} "
            f"({ing['ingredient__measurement_unit']}) — {ing['total']}"
            for ing in ingredients
        ]
        content = "\n".join(lines)
        response = FileResponse(
            content,
            content_type='text/plain',
            filename='shopping_list.txt'
        )
        return response
