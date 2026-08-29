from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(method='filter_tags')
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.NumberFilter(method='filter_favorited')
    is_in_shopping_cart = filters.NumberFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_tags(self, queryset, name, value):
        tags_list = self.request.query_params.getlist('tags')
        if not tags_list:
            return queryset
        tags_slugs = [slug.strip() for slug in tags_list if slug.strip()]
        if not tags_slugs:
            return queryset
        return queryset.filter(tags__slug__in=tags_slugs).distinct()

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            if str(value) in ('1', 'true', 'True'):
                return queryset.filter(favorites__user=user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            if str(value) in ('1', 'true', 'True'):
                return queryset.filter(shoppingcarts__user=user)
        return queryset
