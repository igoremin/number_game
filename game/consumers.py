import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer, WebsocketConsumer
from .models import WaitingUsers, Game
from asgiref.sync import async_to_sync
from random import choice


class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.accept()
        try:
            game = self.user.games.filter(game_ended=False).last()
        except AttributeError:
            return

        if game and game.users.all().count() == 2:
            async_to_sync(self.channel_layer.group_add)(
                f'game__{game.pk}',
                self.channel_name
            )
            if len(self.channel_layer.groups[f'game__{game.pk}']) == 2:
                game.set_start_time_for_current_move()
                async_to_sync(self.channel_layer.group_send)(f'game__{game.pk}', {
                    'type': 'send_message',
                    'message': {
                        'first_move': game.next_move.username,
                        'timer': 20
                    },
                    "event": "USERS_READY"
                })
            elif len(self.channel_layer.groups[f'game__{game.pk}']) > 2:
                self.send(text_data=json.dumps(
                    {
                        "payload": {
                            'type': 'send_message',
                            'message': {
                                'first_move': game.next_move.username,
                                'timer': game.get_timer_for_current_move()
                            },
                            "event": "USERS_READY"
                        }
                    }
                ))

    def disconnect(self, close_code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        response = json.loads(text_data)
        event = response.get("event", None)
        message = response.get("message", None)

        if event == 'FIND_GAME':
            waiting_user = WaitingUsers.get_wait_user()
            if waiting_user != self.user and waiting_user:
                game = waiting_user.games.all().last()
                if game:
                    game.users.add(self.user)
                    game.create_new_move()
                    async_to_sync(self.channel_layer.group_add)(
                        f'find_game__{game.pk}',
                        self.channel_name
                    )
                    async_to_sync(self.channel_layer.group_send)(f'find_game__{game.pk}', {
                        'type': 'send_message',
                        'message': '',
                        "event": "GAME_FIND"
                    })
            else:
                wait_user = WaitingUsers(user=self.user)
                wait_user.save()
                wait_user.create_game()
                async_to_sync(self.channel_layer.group_add)(
                    f'find_game__{wait_user.game.pk}',
                    self.channel_name
                )

        elif event == 'STOP_FIND':
            game = self.user.games.filter(game_ended=False).last()
            game.delete()
            self.send(text_data=json.dumps(
                {
                    "payload": {
                        'type': 'send_message',
                        'message': '',
                        "event": "STOP_WAIT"
                    }
                }
            ))

        elif event == 'GET_HISTORY':
            active_game = self.user.games.filter(game_ended=False).last()

            self.send(text_data=json.dumps(
                {
                    "payload": {
                        "type": "send_message",
                        'message': {
                            'moves_history': active_game.get_moves(),
                            'next_move': active_game.next_move.username,
                        },
                        "event": "HISTORY"}
                }
            ))

        elif event == 'NEW_USER_NUMBER':
            active_game = self.user.games.filter(game_ended=False).last()
            move = active_game.moves.all().get(user=self.user, step=active_game.current_step)
            add_new_row = False
            number = message['number']
            timer_ended = message['timer_ended']
            target_number = None
            winner = None
            if timer_ended:
                move = active_game.moves.filter(step=active_game.current_step).exclude(user=self.user).first()
                lose_move = active_game.moves.get(step=active_game.current_step, user=self.user)
                lose_move.add_number_to_move(0)
                move.is_winner = True
                if move.user_number is None:
                    move.user_number = 0
                move.save()
                next_move = active_game.need_next_move(set_move_winner=False)
            else:
                move.add_number_to_move(number)
                next_move = active_game.need_next_move()

            if next_move:
                if not active_game.game_ended:
                    add_new_row = True
                    target_number = active_game.hidden_numbers.filter(step=active_game.current_step - 1)[0].number
                    winner = active_game.get_move_winner(active_game.current_step - 1)
                else:
                    target_number = active_game.hidden_numbers.filter(step=active_game.current_step)[0].number
                    winner = active_game.get_move_winner(active_game.current_step)
            else:
                active_game.change_next_move_user()
            active_game.set_start_time_for_current_move()

            async_to_sync(self.channel_layer.group_send)(f'game__{active_game.pk}', {
                'type': 'send_message',
                'message': {
                    "result": True,
                    'number': number,
                    'user': self.user.username,
                    'add_new_row': add_new_row,
                    'move_number': active_game.current_step,
                    'target_number': target_number,
                    'winner': winner,
                },
                "event": "MOVE"
            })

            if active_game.game_ended:
                async_to_sync(self.channel_layer.group_send)(f'game__{active_game.pk}', {
                    'type': 'send_message',
                    'message': {
                        'game_winner': active_game.get_game_winner(),
                    },
                    "event": "GAME_END"
                })

        elif event == 'START_GAME':
            game = self.user.games.all().last()
            async_to_sync(self.channel_layer.group_add)(
                f'game__{game.pk}',
                self.channel_name
            )

        elif event == 'LEFT_GAME':
            game = self.user.games.all().last()
            game.game_winner = game.users.exclude(pk=self.user.pk).first()
            game.game_ended = True
            game.save()

            async_to_sync(self.channel_layer.group_send)(f'game__{game.pk}', {
                'type': 'send_message',
                'message': {
                    'game_winner': game.get_game_winner(),
                },
                "event": "GAME_END"
            })

    def send_message(self, res):
        """ Receive message from room group """
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            "payload": res,
        }))
