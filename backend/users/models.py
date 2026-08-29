from django.contrib.auth.models import AbstractUser
from django.db import models

from constants import (
    MAX_LENGTH_USER_EMAIL, MAX_LENGTH_USER_FIRST_NAME,
    MAX_LENGTH_USER_LAST_NAME,
)


class User(AbstractUser):
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        blank=True,
        null=True
    )
    email = models.EmailField(
        'email',
        max_length=MAX_LENGTH_USER_EMAIL,
        unique=True
        blank=False
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_USER_FIRST_NAME,
        blank=False
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_USER_LAST_NAME,
        blank=False
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки на автора."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
