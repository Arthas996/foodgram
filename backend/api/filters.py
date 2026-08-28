from django_filters import rest_framework as filters
from .models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(method='filter_tags')
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.NumberFilter(method='filter_favorited')
    is_in_shopping_cart = filters.NumberFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_tags(self, queryset, name, value):
        if not value:
            return queryset
        tags_slugs = [slug.strip() for slug in value.split(',') if slug.strip()]
        return queryset.filter(tags__slug__in=tags_slugs).distinct()

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            if user.is_authenticated:
                return queryset.filter(favorited_by__user=user)
            return queryset.none()
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            if user.is_authenticated:
                return queryset.filter(in_shopping_cart__user=user)
            return queryset.none()
        return queryset
