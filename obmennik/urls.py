from django.contrib import admin
from django.urls import path

from obmennik.view import UserViewSet, CurrencyViewSet, OfferViewSet, SessionViewSet

urlpatterns = [
    path('user/create/', UserViewSet.as_view({"post": "create_user"}), name='create_user'),
    path('user/getOffers/', UserViewSet.as_view({"get": "get_user_offers"}), name='get_user_offers'),
    path('user/watchlist/', UserViewSet.as_view({"get": "get_user_watchlist"}), name='get_user_watchlist'),
    path('user/addWatchlist/', UserViewSet.as_view({"post": "add_watchlist"}), name='add_watchlist'),
    path('user/removeWatchlist/', UserViewSet.as_view({"post": "remove_watchlist"}), name='add_watchlist'),
    path('user/rename/', UserViewSet.as_view({"post": "rename"}), name='user_rename'),
    path('user/info/', UserViewSet.as_view({"get": "info"}), name='user_info'),
    path('user/updateRating/', UserViewSet.as_view({"post": "update_rating"}), name='update_rating'),

    path('currency/getList/', CurrencyViewSet.as_view({"get": "get_list_currencies"}), name='get_currency'),
    path('currency/add/', CurrencyViewSet.as_view({"post": "add_currency"}), name='create_currency'),

    path('offer/create/', OfferViewSet.as_view({"post": "create_offer"}), name='create_offer'),
    path('offer/getList/', OfferViewSet.as_view({"get": "get_all_offers"}), name='get_all_offers'),
    path('offer/edit/', OfferViewSet.as_view({"post": "edit_offer"}), name='edit_offer'),

    path('session/create/', SessionViewSet.as_view({"post": "create_session"}), name='create_session'),
    path('session/sendMessage/', SessionViewSet.as_view({"post": "send_message"}), name='send_message'),
    path('session/list/', SessionViewSet.as_view({"get": "get_list"}), name='get_session_list'),
    path('session/close/', SessionViewSet.as_view({"post": "close"}), name='session_close'),
]
