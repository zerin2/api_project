import random

from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

import api.constants as const
from api_yamdb import settings
from reviews.constants import PROFILE_URL_NAME
from reviews.models import User, Category, Genre, Title, Review
from .filters import TitleFilter
from .permissions import (
    AdminOnlyPermission,
    AdminOrSafeMethodPermission,
    IsAuthorModeratorAdminOrReadOnly,
)
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    GetTokenSerializer,
    ReviewSerializer,
    TitleReadSerializer,
    TitleCreateUpdateSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from .utilits import send_confirmation_code


class UserViewSet(viewsets.ModelViewSet):
    """
    Представление для реализации операций для
    кастомной модели пользователя.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    permission_classes = (AdminOnlyPermission,)
    http_method_names = const.ALLOWED_HTTP_METHODS

    @action(
        methods=['GET', 'PATCH'],
        url_path=PROFILE_URL_NAME,
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def profile(self, request):
        """Получение или обновление данных пользователя."""
        if request.method != 'PATCH':
            return Response(UserSerializer(request.user).data)
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


def get_confirmation_code():
    return (''.join(random.choices(
        settings.CONFIRMATION_CODE_CHARACTERS,
        k=settings.CONFIRMATION_CODE_LENGTH
    )))


@api_view(['POST'])
@permission_classes([permissions.AllowAny], )
def register_user(request):
    """Регистрация нового пользователя."""
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user, _ = User.objects.get_or_create(
            email=serializer.validated_data['email'],
            username=serializer.validated_data['username'],
        )
    except IntegrityError:
        raise ValidationError(
            const.EMAIL_REGISTER_ERROR
            if User.objects.filter(
                username=serializer.validated_data['username']
            ).exists()
            else const.USER_REGISTER_ERROR
        )
    user.confirmation_code = get_confirmation_code()
    user.save()
    send_confirmation_code(user, user.confirmation_code)
    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny], )
def get_user_token(request):
    """Получения токена пользователя."""
    serializer = GetTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User,
        username=serializer.validated_data['username']
    )
    input_code = serializer.validated_data['confirmation_code']
    if user.confirmation_code != input_code:
        if user.confirmation_code != settings.DEFAULT_CONFIRMATION_CODE:
            user.confirmation_code = settings.DEFAULT_CONFIRMATION_CODE
            user.save()
        raise ValidationError(const.CONFIRMATION_CODE_ERROR)
    return Response(
        {'token': str(AccessToken.for_user(user))},
        status=status.HTTP_200_OK
    )


class ContentGroupsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Представление для работы с категориями и жанрами."""
    permission_classes = (AdminOrSafeMethodPermission,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'
    http_method_names = const.ALLOWED_HTTP_METHODS_CATEGORY_GENRE


class GenreViewSet(ContentGroupsViewSet):
    """Представление для работы только с жанрами."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class CategoryViewSet(ContentGroupsViewSet):
    """Представление для работы только с категориями."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TitleViewSet(viewsets.ModelViewSet):
    """Представление для работы с произведениями."""
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).order_by(*Title._meta.ordering)
    permission_classes = (AdminOrSafeMethodPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    http_method_names = const.ALLOWED_HTTP_METHODS

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleCreateUpdateSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Представление для реализации операций
    для модели отзывов на произведени.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthorModeratorAdminOrReadOnly]
    http_method_names = const.ALLOWED_HTTP_METHODS

    def get_title(self):
        return get_object_or_404(Title, pk=self.kwargs['title_id'])

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(viewsets.ModelViewSet):
    """
    Представление для реализации операций
    для модели комментариев к отзывам на произведения.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorModeratorAdminOrReadOnly]
    http_method_names = const.ALLOWED_HTTP_METHODS

    def get_review(self):
        return get_object_or_404(Review, pk=self.kwargs['review_id'])

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        review = self.get_review()
        serializer.save(
            author=self.request.user,
            review=review,
            title=review.title)
