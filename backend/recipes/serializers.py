import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для рецептов (избранное, корзина, подписки)."""
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Полный сериализатор для рецепта (GET)."""
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для создания ингредиентов в рецепте."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""
    id = serializers.IntegerField(read_only=True)
    image = serializers.CharField(write_only=True)
    ingredients = RecipeIngredientCreateSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text',
            'cooking_time', 'ingredients', 'tags'
        )

    def validate_image(self, value):
        if not value.startswith('data:image'):
            raise serializers.ValidationError('Неверный формат изображения')
        return value

    def create(self, validated_data):
        image_data = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context.get('request').user
        validated_data.pop('author', None)

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)

        for ing in ingredients_data:
            ingredient_id = ing.get('id')
            amount = ing.get('amount')
            if not ingredient_id:
                continue
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_id,
                amount=amount
            )

        self._save_image(recipe, image_data)
        return recipe

    def update(self, instance, validated_data):
        if 'image' in validated_data:
            self._save_image(instance, validated_data.pop('image'))

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )

        if 'tags' in validated_data:
            instance.tags.set(validated_data['tags'])

        if 'ingredients' in validated_data:
            instance.recipe_ingredients.all().delete()
            for ing in validated_data['ingredients']:
                ingredient_id = ing.get('id')
                amount = ing.get('amount')
                if ingredient_id:
                    RecipeIngredient.objects.create(
                        recipe=instance,
                        ingredient_id=ingredient_id,
                        amount=amount
                    )

        instance.save()
        return instance

    def _save_image(self, recipe, image_data):
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        data = ContentFile(
            base64.b64decode(imgstr),
            name=f'{recipe.id}.{ext}'
        )
        recipe.image.save(data.name, data, save=True)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        extra_kwargs = {
            'user': {'read_only': True},
            'recipe': {'read_only': True}
        }


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        extra_kwargs = {
            'user': {'read_only': True},
            'recipe': {'read_only': True}
        }
