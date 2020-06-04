from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import JsonWebsocketConsumer
import json
from .models import Game, Profile
from django.core import serializers

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        me = self.scope['user']
        game = Game.get_game(self.scope['url_route']['kwargs']['room_name'])
        if game.status == "completed":
            async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'close_message',
                'message': "closed"
            })
        else:
            if game.firstPlayer is None:
                game.set_firstPlayer(me)
            if game.secondPlayer is None and me.id != game.firstPlayer.id:
                game.set_secondPlayer(me)
            if game.firstPlayer is not None and game.secondPlayer is not None:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'users_message',
                        'message': '2players',
                        'firstPlayer': game.firstPlayer.username,
                        'secondPlayer': game.secondPlayer.username
                    }
                )

        self.accept()

    def users_message(self, event):
        message = event['message']
        firstPlayer = event['firstPlayer']
        secondPlayer = event['secondPlayer']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'firstPlayer': firstPlayer,
            'secondPlayer': secondPlayer
        }))

    def disconnect(self, close_code):
        # Leave room group
        game = Game.get_game(self.scope['url_route']['kwargs']['room_name'])

        me = self.scope['user']
        if me == game.secondPlayer and game.secondPlayer_choice is None:
            game.secondPlayer = None
            game.set_status("waiting")
            game.save()

        if me == game.firstPlayer and game.firstPlayer_choice is None:
            game.firstPlayer = None
            game.set_status("waiting")
            game.save()




        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'users_message',
                'message': 'waiting',
                'firstPlayer': "",
                'secondPlayer': ""
            }
        )

        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')

        me = self.scope['user']
        game = Game.get_game(self.scope['url_route']['kwargs']['room_name'])

        if me.username == game.firstPlayer.username:
            game.make_first_player_choice(message)
        elif me.username == game.secondPlayer.username:
            game.make_second_player_choice(message)

        result = ""

        if game.firstPlayer_choice is not None and game.secondPlayer_choice is not None:
            result = game.result()

        profile = Profile.get_profile(me)

        winner = ""
        isCompleted=""
        if game.winner is not None:
            winner = game.winner.username
            isCompleted="completed"
            if game.firstPlayer.username == winner:
                profile.change_profile(game.firstPlayer, 1)
                profile.change_profile(game.secondPlayer, 0)
            else:
                profile.change_profile(game.firstPlayer, 0)
                profile.change_profile(game.secondPlayer, 1)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': isCompleted,
                'username': me.username,
                'winner': winner,
                'result': result
                }
            )



    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        username = event['username']
        winner = event['winner']
        result = event['result']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'winner': winner,
            'result': result
        }))

    def close_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
        }))

class LobbyConsumer(WebsocketConsumer):
        def connect(self):
            self.room_group_name = "lobby"
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            self.accept()

        def disconnect(self, close_code):
            pass

        def receive(self, text_data):
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            me = self.scope['user']
            action = text_data_json['action']
            if action == "random":
                randomGame = ""
                if Game.get_available_games().count() != 0:
                    randomGame = Game.get_random().game_id

                self.send(text_data=json.dumps({
                    'type': 'response_message',
                    'message': "random",
                    'randomgame': randomGame
                }))

            if action == "create":
                game = Game.objects.filter(game_id=message)

                if game.exists() | (not bool(message and message.strip())):
                    message = "deny"
                else:
                    game = Game.create_new(message,  me)
                    message = "accept"

                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': "new_game",
                            'username': game.firstPlayer.username,
                            'name': game.game_id

                        }
                    )


                self.send(text_data=json.dumps({
                    'type': 'response_message',
                    'message': message,
                }))



        # Receive message from room group
        def chat_message(self, event):
            message = event['message']
            username = event['username']
            name = event['name']

            # Send message to WebSocket
            self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                'name': name
            }))

        def response_message(self, event):
            message = event['message']
            game_id=event['game_id']
            game_firstPlayer=event['game_firstPlayer']
            randomgame = event['']

            # Send message to WebSocket
            self.send(text_data=json.dumps({
                'message': message,
                'game_id': game_id,
                'game_firstPlayer': game_firstPlayer
            }))
