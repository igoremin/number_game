from django.conf.urls import url
from django.urls import path
from game.consumers import GameConsumer

websocket_urlpatterns = [
    path('new_game/', GameConsumer.as_asgi()),
    # path('new_game/', GameConsumer.as_asgi()),
]