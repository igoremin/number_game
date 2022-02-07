from django.db import models
from django.contrib.auth.models import User
from random import randint
from datetime import datetime
from django.utils.timezone import get_current_timezone
from random import choice


class Game(models.Model):
    is_active = models.BooleanField(verbose_name='Статус игры', default=True)
    current_step = models.IntegerField(verbose_name='Номер текущего хода', default=0)
    users = models.ManyToManyField(User, related_name='games', verbose_name='Игроки')
    game_winner = models.ForeignKey(User, related_name='winner_games', verbose_name='Победитель',
                                    on_delete=models.CASCADE, blank=True, null=True)
    game_ended = models.BooleanField(verbose_name='Игра окончена', default=False)
    date = models.DateTimeField(verbose_name='Дата и время игры', blank=True, null=True)
    next_move = models.ForeignKey(User, verbose_name='Следующий ход у пользователя', on_delete=models.CASCADE,
                                  blank=True, null=True)

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'

    def __str__(self):
        return f'Game : {self.pk}'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.date = datetime.now(tz=get_current_timezone())
        super().save(*args, **kwargs)

    @staticmethod
    def create_new_game(user_1, user_2):
        new_game = Game()
        new_game.save()
        new_game.users.add(user_1)
        new_game.users.add(user_2)
        new_game.create_new_move()
        return new_game

    @staticmethod
    def create_empty_game():
        new_game = Game()
        new_game.save()
        return new_game

    @staticmethod
    def get_history_for_user(user_pk):
        # Получение данных об играх для пользователя
        user = User.objects.get(pk=user_pk)
        all_games = user.games.filter(game_ended=True)
        data = []
        for game in all_games:
            game_data = {'date': game.date, 'enemy': game.users.exclude(pk=user.pk)[0].username}
            if game.game_winner:
                if user == game.game_winner:
                    game_data.update(result='Победа')
                else:
                    game_data.update(result='Поражение')
            else:
                game_data.update(result='Ничья')
            data.append(game_data)
        return data

    def set_start_time_for_current_move(self):
        # Установка начального времени хода
        move = self.moves.filter(user=self.next_move, step=self.current_step).first()
        move.set_time()

    def get_timer_for_current_move(self):
        # Получение остатка времени для текущего хода
        return self.moves.filter(user=self.next_move, step=self.current_step).first().get_current_timer()

    def get_moves(self):
        # Получение истории ходов для заполнения игровой таблицы во время игры
        result = []
        users = self.users.all()
        user_1, user_2 = users[0], users[1]
        for step in range(1, self.current_step + 1):
            target_number = '?'
            winner = self.get_move_winner(step)
            move_ended = False
            if len(self.moves.filter(step=step, user_number__isnull=False)) == 2:
                move_ended = True
                target_number = self.hidden_numbers.filter(step=step)[0].number
            user_1_number = Move.objects.get(game=self, user=user_1, step=step).user_number
            user_2_number = Move.objects.get(game=self, user=user_2, step=step).user_number

            data = {
                'winner': winner,
                'move_ended': move_ended,
                'step': step,
                'user_1': {'name': user_1.username, 'number': user_1_number},
                'user_2': {'name': user_2.username, 'number': user_2_number},
                'target_number': target_number
                }
            result.append(data)
        return result

    def need_next_move(self, set_move_winner=True):
        # Проверка нужен ли следующий ход в игре
        last_moves = self.moves.filter(step=self.current_step, user_number__isnull=False)
        if len(last_moves) != 2:
            return False    # Если оба игрока не установили значение в последнем ходе, тогда ход не нужен
        if set_move_winner:
            self.set_move_winner()
        all_moves = self.moves.filter(user_number__isnull=False)
        if len(all_moves) == 10:
            self.set_game_winner()  # Если общее количество ходов у обоих игроков = 10, определяется победитель игры
        if not self.game_ended:
            self.create_new_move()  # Если игра не закончена, создается новый ход
        return True

    def create_new_move(self):
        # Создание нового хода для игры
        self.add_step()
        # Создание отдельного хода для каждого игрока
        Move(user=self.users.all()[0], game=self).save()
        Move(user=self.users.all()[1], game=self).save()
        # Определение игрока для текущего хода
        if not self.next_move:
            self.next_move = choice(self.users.all())
        else:
            self.next_move = self.users.exclude(pk=self.next_move.pk)[0]
        self.save()
        TargetNumber(game=self).save()

    def add_step(self):
        # Увеличение счетчика ходов
        self.current_step += 1
        self.save()

    def set_move_winner(self):
        # Установка победителя для текущего хода игры
        moves = self.moves.filter(step=self.current_step, user_number__isnull=False)
        target_number = self.hidden_numbers.filter(step=self.current_step)
        if len(moves) == 2 and target_number:   # проверка что у обоих игроков есть число для последенго хода
            target_number = target_number[0].number
            if abs(moves[0].user_number - target_number) > abs(moves[1].user_number - target_number):
                moves[1].is_winner = True
                moves[1].save()
            elif abs(moves[0].user_number - target_number) < abs(moves[1].user_number - target_number):
                moves[0].is_winner = True
                moves[0].save()

    def get_move_winner(self, move=None):
        # Получение победителя текущего либо определенного хода игры (если он есть)
        if move is None:
            move = self.current_step
        winner = self.moves.filter(step=move, is_winner=True)
        if winner:
            return winner[0].user.username
        return 'not_winner'

    def get_game_winner(self):
        # Получение победителя игры (если он есть)
        if self.game_winner:
            return self.game_winner.username
        return 'not_winner'

    def set_game_winner(self):
        # Установка победителя для всей игры
        users = self.users.all()
        user_1, user_2 = users[0], users[1]
        user_1_winners = self.moves.filter(user=user_1, is_winner=True) # Игры с победой у первого игрока
        user_2_winners = self.moves.filter(user=user_2, is_winner=True) # Игры с победой у второго игрока
        # Определение победителя. Если победителя нет, оставляем поле пустым
        if len(user_1_winners) > len(user_2_winners):
            self.game_winner = user_1
        elif len(user_2_winners) > len(user_1_winners):
            self.game_winner = user_2
        self.game_ended = True  # Изменнеие статуса игры
        self.save()

    def change_next_move_user(self):
        # Определение хода следующего игрока
        self.next_move = self.users.exclude(pk=self.next_move.pk)[0]
        self.save()


class Move(models.Model):
    user = models.ForeignKey(User, verbose_name='Игрок', on_delete=models.PROTECT)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name='Игра', related_name='moves')
    step = models.IntegerField(verbose_name='Номер хода', default=1)
    user_number = models.IntegerField(verbose_name='Число игрока', blank=True, null=True)
    is_winner = models.BooleanField(verbose_name='Победитель', default=False)
    move_start_time = models.DateTimeField(verbose_name='Время начала хода', blank=True, null=True)

    class Meta:
        verbose_name = 'Ход'
        verbose_name_plural = 'Список ходов'

    def __str__(self):
        return f'Game : {self.game.pk}, move : {self.step}'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.step = self.game.current_step
        super().save(*args, **kwargs)

    def add_number_to_move(self, number):
        # Добавление числа к текущему ходу
        if self.user_number is None:
            self.user_number = number
            self.save()

    def set_time(self):
        self.move_start_time = datetime.now(tz=get_current_timezone())
        self.save()

    def get_current_timer(self):
        delta_time = (datetime.now(tz=get_current_timezone()) - self.move_start_time).seconds
        if delta_time < 20:
            return 20 - delta_time
        return 0


class TargetNumber(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name='Игра', related_name='hidden_numbers')
    number = models.IntegerField(verbose_name='Загаданное число', default=0)
    step = models.IntegerField(verbose_name='Номер хода', default=1)

    class Meta:
        verbose_name = 'Загаданное значение'
        verbose_name_plural = 'Загаданные значения'

    def __str__(self):
        return f'Game : {self.game.pk}, number : {self.number}'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.number = randint(1, 20)
            self.step = self.game.current_step
        super().save(*args, **kwargs)


class WaitingUsers(models.Model):
    """Возможно класс лишний, свойство ожидания игры можно задать конкретному игроку.
    В списке ожидания всегда должен быть только один игрок"""
    user = models.ForeignKey(User, verbose_name='Игрок', on_delete=models.CASCADE)
    start_wait_time = models.DateTimeField(verbose_name='Время начала ожидания игры')
    game = models.ForeignKey(Game, verbose_name='Игра', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = 'Пользователь ожидающий игры'
        verbose_name_plural = 'Пользователи ожидающие игры'

    @staticmethod
    def get_wait_user():
        # получение первого пользователя в очереди
        all_waiting_users = WaitingUsers.objects.all().order_by('start_wait_time')
        if all_waiting_users:
            user_pk = all_waiting_users[0].user.pk
            all_waiting_users[0].delete()
            return User.objects.get(pk=user_pk)
        else:
            return False

    def save(self, *args, **kwargs):
        if not self.pk:
            self.start_wait_time = datetime.now(tz=get_current_timezone())
        super().save(*args, **kwargs)

    def create_game(self):
        self.game = Game.create_empty_game()
        self.game.users.add(self.user)
        self.save()
