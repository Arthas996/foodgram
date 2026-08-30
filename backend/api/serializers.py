from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)

from constants import MIN_INGREDIENT_AMOUNT
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import User


# Пояснение к классу UserCreateSerializer:
# Стандартный сериализатор Djoser
# не включает обязательные поля first_name и last_name.
# Для соответствия требованиям API (и тестам Postman)
# я оставил кастомный сериализатор, который делает эти поля обязательными.
# Это минимальное и оправданное расширение, без которого
# функциональность регистрации не работала бы корректно.
class UserCreateSerializer(DjoserUserCreateSerializer):
    """
    Сериализатор для регистрации пользователя.
    """

    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password'
        )
        extra_kwargs = {'password': {'write_only': True}}


class UserSerializer(DjoserUserSerializer):
    """
    Сериализатор для модели пользователя с полями is_subscribed и avatar.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.follower.filter(author=obj).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вывода ингредиентов в рецепте.
    """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Краткий сериализатор для рецептов (избранное, корзина, подписки).
    """

    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipesSerializer(UserSerializer):
    """
    Сериализатор для пользователя с его рецептами (для подписок).
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request:
            return []
        limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        return RecipeShortSerializer(
            queryset,
            many=True,
            context={'request': request}
        ).data


class RecipeSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для рецепта (только чтение).
    """

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
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.shoppingcarts.filter(recipe=obj).exists()
        )


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """
    Сериализатор для создания ингредиентов в рецепте.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецепта.
    """

    id = serializers.IntegerField(read_only=True)
    image = Base64ImageField()
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

    def validate(self, data):
        if self.instance:  # обновление
            if 'ingredients' not in data or not data.get('ingredients'):
                raise serializers.ValidationError(
                    {'ingredients': 'Это поле обязательно и не должно быть пустым.'}
                )
            if 'tags' not in data or not data.get('tags'):
                raise serializers.ValidationError(
                    {'tags': 'Это поле обязательно и не должно быть пустым.'}
                )
        else:  # создание
            if not data.get('ingredients'):
                raise serializers.ValidationError(
                    {'ingredients': 'Необходимо указать хотя бы один ингредиент.'}
                )
            if not data.get('tags'):
                raise serializers.ValidationError(
                    {'tags': 'Необходимо указать хотя бы один тег.'}
                )
        if not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Изображение обязательно.'}
            )
        return data

    def validate_ingredients(self, value):
        ids = [item['id'].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return value

    def validate_tags(self, value):
        ids = [tag.id for tag in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        validated_data.pop('author', None)
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self._add_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags'))
        if 'ingredients' in validated_data:
            instance.recipe_ingredients.all().delete()
            ingredients_data = validated_data.pop('ingredients')
            self._add_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def _add_ingredients(self, recipe, ingredients_data):
        ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ing['id'],
                amount=ing['amount']
            )
            for ing in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(ingredients)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Favorite (избранное)."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        extra_kwargs = {
            'user': {'read_only': True},
            'recipe': {'read_only': True}
        }


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart (список покупок)."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        extra_kwargs = {
            'user': {'read_only': True},
            'recipe': {'read_only': True}
        }
