from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import json


class Game(models.Model):
    game_id = models.TextField(max_length=50, unique=True, blank=True)
    BET = (
        ('stone', 'stone'),
        ('paper', 'paper'),
        ('scissors', 'scissors'),
       
    )
    #creator
    firstPlayer = models.ForeignKey(
        User, null=True, related_name='firstPlayer', on_delete=models.DO_NOTHING)
    #enemy
    secondPlayer = models.ForeignKey(
        User, related_name='secondPlayer', null=True, blank=True, on_delete=models.DO_NOTHING)
    winner = models.ForeignKey(
        User, related_name='winner', null=True, blank=True, on_delete=models.DO_NOTHING)
    completed = models.DateTimeField(null=True, blank=True)
    firstPlayer_choice = models.TextField(blank=True, choices=BET)
    secondPlayer_choice = models.TextField(blank=True, choices=BET)

    GAME_STATUS = (
        ('waiting', 'waiting'),
        ('completed', 'completed'),
        ('playing', 'playing'),
    )
    status = models.TextField(choices=GAME_STATUS, default='waiting')


    @staticmethod
    def get_available_games():
        return Game.objects.filter(status__exact="waiting").order_by('game_id')[:20]

    @staticmethod
    def get_games_for_player(user):
        from django.db.models import Q
        return Game.objects.filter(Q(secondPlayer=user) | Q(firstPlayer=user) & Q(status="completed"))

    @staticmethod
    def get_completed_games():
        return Game.objects.filter(status="completed").order_by('completed')

    @staticmethod
    def create_new(name, user):
        new_game = Game(firstPlayer=user, game_id=name)
        new_game.save()
        return new_game

    def set_completed(self, winner):
        self.winner = winner
        self.save(update_fields=["winner"])
        self.completed = datetime.now()
        self.save(update_fields=["completed"])
        self.set_status("completed")
        self.save(update_fields=["status"])

    def set_firstPlayer(self, user):
        self.firstPlayer = User.objects.filter(username=user)[0]
        self.save(update_fields=["firstPlayer"])

    def set_secondPlayer(self, user):
        self.secondPlayer = User.objects.filter(username=user)[0]
        self.set_status("playing")
        self.save(update_fields=["secondPlayer"])

    def set_status(self, status):
        self.status = status
        self.save(update_fields=["status"])

    @staticmethod
    def get_game(name):
        game = Game.objects.filter(game_id=name)
        if game.exists():
            game = game.first()
        return game

    def __str__(self):
        return self.game_id

    def result(self):
        result = ""
        if self.firstPlayer_choice == self.secondPlayer_choice:
            self.secondPlayer_choice = ""
            self.firstPlayer_choice = ""
            self.save(update_fields=["firstPlayer_choice", "secondPlayer_choice"])
            return "noone"
        elif self.firstPlayer_choice == 'stone':
            if self.secondPlayer_choice == 'scissors':
                self.set_completed(self.firstPlayer)
            else:
                self.set_completed(self.secondPlayer)
        elif self.firstPlayer_choice == "paper":
            if self.secondPlayer_choice == 'stone':
                self.set_completed(self.firstPlayer)
            else:
                self.set_completed(self.secondPlayer)
        elif self.firstPlayer_choice == "scissors":
            if self.secondPlayer_choice == "paper":
                self.set_completed(self.firstPlayer)
            else:
                self.set_completed(self.secondPlayer)

    def make_first_player_choice(self, message):
        self.firstPlayer_choice = message
        self.save(update_fields=["firstPlayer_choice"])

    def make_second_player_choice(self, message):
        self.secondPlayer_choice = message
        self.save(update_fields=["secondPlayer_choice"])

    @staticmethod
    def get_random():
        if Game.objects.filter(status__exact="waiting") is not None:
            return Game.objects.filter(status__exact="waiting").order_by("?").first()


class Profile(models.Model):
    user = models.ForeignKey(User, related_name='player', on_delete=models.CASCADE)
    wins = models.IntegerField(blank=True, default=0)
    losings = models.IntegerField(blank=True, default=0)
    rating = models.FloatField(blank=True, default=0)

    @staticmethod
    def create_new_profile(user):
        new_profile = Profile(user=user)
        new_profile.save()
        return new_profile

    @staticmethod
    def get_profile(user):
        profile = Profile.objects.filter(user=user)
        if profile.exists():
            profile = profile.first()
        else:
            profile = Profile.create_new_profile(user)
        return profile

    def profile_wins(self):
        self.wins += 1
        self.save(update_fields=['wins'])
        self.profile_rating_update()


    def profile_loses(self):
        self.losings += 1
        self.save(update_fields=['losings'])
        self.profile_rating_update()


    def profile_rating_update(self):
        if self.losings == 0:
            rat = self.wins
        else:
            rat = self.wins/self.losings
        self.rating = rat
        self.save(update_fields=['rating'])

    @staticmethod
    def change_profile(user, isWinner):
        profile = Profile.get_profile(user)
        if isWinner == 1:
            profile.profile_wins()
        else:
            profile.profile_loses()

