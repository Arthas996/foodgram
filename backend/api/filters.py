from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для модели Recipe.

    Позволяет фильтровать рецепты по тегам (пересечение), автору,
    наличию в избранном и списке покупок.
    """

    # Используем AllValuesMultipleFilter для корректной обработки множественных
    # значений параметра tags, но с кастомным методом для реализации AND.
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        method='filter_tags'
    )
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_tags(self, queryset, name, value):
        """
        Фильтрует рецепты по пересечению всех переданных тегов (AND).
        Ожидается параметр ?tags=slug1&tags=slug2
        """
        if not value:
            return queryset
        for slug in value:
            if slug:
                queryset = queryset.filter(tags__slug=slug)
        return queryset.distinct()

    def filter_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shoppingcarts__user=self.request.user)
        return queryset
