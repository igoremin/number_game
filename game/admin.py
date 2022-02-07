from django.contrib import admin
from .models import Game, WaitingUsers, Move, TargetNumber


admin.site.register(Game)
admin.site.register(WaitingUsers)
admin.site.register(Move)
admin.site.register(TargetNumber)
