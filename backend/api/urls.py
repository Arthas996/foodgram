from django.urls import include, path
from rest_framework.routers import DefaultRouter
from djoser.views import UserViewSet as DjoserUserViewSet

from users.views import UserViewSet, AvatarView
from recipes.views import TagViewSet, IngredientViewSet, RecipeViewSet


router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

set_password_view = DjoserUserViewSet.as_view({'post': 'set_password'})

urlpatterns = [
    path('users/me/avatar/', AvatarView.as_view(), name='avatar'),
    path('users/set_password/', set_password_view, name='set_password'),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
