import json
import random
from threading import Timer, Thread, Event
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

users = []
rooms = []
startArray = []
question = []
user = []
cards = []
round2 = []
colors = ['h', 'd', 's', 'c']

class perpetualTimer():

   def __init__(self, t, hFunction):
      self.t = t
      self.hFunction = hFunction
      self.thread = Timer(self.t, self.handle_function)

   def handle_function(self):
      self.hFunction()
      self.thread = Timer(self.t, self.handle_function)
      self.thread.start()

   def start(self):
      self.thread.start()

   def cancel(self):
      self.thread.cancel()


class ChatConsumer(WebsocketConsumer):

    def remove(self):
        del startArray[rooms.index(self.room_group_name)]
        del users[rooms.index(self.room_group_name)]
        rooms.remove(self.room_group_name)

    def connect(self):
        global rooms
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'room_%s' % self.room_name
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        if self.room_group_name not in rooms:
            rooms.append(self.room_group_name)
            users.append([])
            question.append(0)
            user.append(0)
            cards.append(create_cards())
            round2.append(0)
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket

    def receive(self, text_data):
        def next_card():
            if round2[rooms.index(self.room_group_name)] < 15:
                card = random.choice(cards[rooms.index(self.room_group_name)])
                cards[rooms.index(self.room_group_name)].remove(card)
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': "?card",
                        'username': "server",
                        'card': card,
                    }
                )
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': "?round2",
                        'username': "server",
                    }
                )
            round2[rooms.index(self.room_group_name)] += 1

        timer = perpetualTimer(8, next_card)

        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']

        if message == '?adduser':
            if username not in users[rooms.index(self.room_group_name)]:
                users[rooms.index(self.room_group_name)].append(username)
                self.send(text_data=json.dumps({
                    'message': "Okay",
                }))
            else:
                self.send(text_data=json.dumps({
                    'message': "Nope",
                }))
        elif message == "/closing_screen":
            users[rooms.index(self.room_group_name)].remove(username)
        elif message == "?round1":
            next_username, turn = letsgo(self)
            if next_username != "done":
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': "?round1",
                        'question': turn,
                        'username': next_username,
                    }
                )
            else:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': "?round2",
                        'username': next_username,
                    }
                )
                timer.start()
        elif message == "?round2":
            if round2[rooms.index(self.room_group_name)] == 0:
                timer.start()
        elif message == "?round3":
            timer.cancel()
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': "?round3",
                    'username': "server",
                }
            )
        elif message == "?drink":
            lie = text_data_json['lie']
            card = text_data_json['card']
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                    'card':card,
                    'lie': lie
                }
            )
        elif message == "?placecard":
            card = text_data_json['card']
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                    'card': card
                }
            )
        elif message == "?question":
            card = random.choice(cards[rooms.index(self.room_group_name)])
            cards[rooms.index(self.room_group_name)].remove(card)
            self.send(text_data=json.dumps({
                'message': "?card",
                'username': username,
                'card': card
            }))
        else:
            # Send message to room group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                }
            )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        username = event['username']

        if message == "?round1":
            quest = event['question']
            self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                'question': quest
            }))
        elif message == "?card" or message == "?placecard":
            card = event['card']
            self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                'card': card
            }))
        elif message == "?drink":
            lie = event['lie']
            card = event['card']
            self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                'card': card,
                'lie': lie
            }))
        else:
            # Send message to WebSocket
            self.send(text_data=json.dumps({
                'message': message,
                'username': username
            }))


def letsgo(self):
    global question
    global user
    self_index = rooms.index(self.room_group_name)

    if question[self_index] > 3:
        return "done", question[self_index]
    elif user[self_index] == 0 and question[self_index] == 0:
        user[self_index] += 1
        return users[self_index][user[self_index] - 1], question[self_index]
    elif len(users[self_index]) == 1:
        user[self_index] = 0
        question[self_index] += 1
        return users[self_index][user[self_index] - 1], question[self_index]
    elif user[self_index] == len(users[self_index]) - 1:
        question[self_index] += 1
        user[self_index] = 0
        return users[self_index][len(users[self_index]) - 1], question[self_index] - 1
    else:
        user[self_index] += 1
        return users[self_index][user[self_index] - 1], question[self_index]


def create_cards():
    deck = []
    for s in colors:
        for i in range(1, 14):
            deck.append(s + str(i))
    return deck
