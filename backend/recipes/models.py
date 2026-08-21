from django.core.validators import MinValueValidator
from django.db import models

from constants import (
    MAX_LENGTH_INGREDIENT_NAME, MAX_LENGTH_INGREDIENT_UNIT,
    MAX_LENGTH_RECIPE_NAME, MAX_LENGTH_TAG_NAME, MAX_LENGTH_TAG_SLUG,
    MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT,
)
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True
    )
    slug = models.SlugField(
        'Слаг',
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_INGREDIENT_NAME
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LENGTH_INGREDIENT_UNIT
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_RECIPE_NAME
    )
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=[MinValueValidator(MIN_COOKING_TIME)]
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} — {self.amount} '
            f'{self.ingredient.measurement_unit}'
        )


class BaseFavoriteShopping(models.Model):
    """Абстрактная модель для избранного и корзины."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s'
            )
        ]

    def __str__(self):
        return f'{self.user} → {self.recipe}'


class Favorite(BaseFavoriteShopping):
    class Meta(BaseFavoriteShopping.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(BaseFavoriteShopping):
    class Meta(BaseFavoriteShopping.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
