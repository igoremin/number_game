from django.urls import path
from .views import main_page, game_page, history

urlpatterns = [
    path('', main_page, name='main_page_url'),
    path('new_game/', game_page, name='game_page_url'),
    path('history/', history, name='history_url'),
]