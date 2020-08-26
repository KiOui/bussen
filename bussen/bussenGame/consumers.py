import json
import random
from time import sleep
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

users = []
rooms = []
startArray = []
question = []
user = []
cards = []
round2 = []
hosts = []
cardsleft = []
colors = ['h', 'd', 's', 'c']
started = []

class ChatConsumer(WebsocketConsumer):

    def connect(self):
        global rooms
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'room_%s' % self.room_name
        # Join room group

        if self.room_group_name not in rooms:
            rooms.append(self.room_group_name)
            users.append([])
            question.append(0)
            user.append(0)
            cards.append(create_cards())
            round2.append(0)
            hosts.append("X")
            cardsleft.append([])
            started.append(False)

        if not started[rooms.index(self.room_group_name)]:
            self.accept()

            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name,
            )


    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            username = text_data_json['username']

            if message == '?adduser':
                if username not in users[rooms.index(self.room_group_name)] and "#" not in username and "server" not in username:
                    users[rooms.index(self.room_group_name)].append(username)
                    self.send(text_data=json.dumps({
                        'message': "Okay",
                    }))
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': "?players",
                            'username': 'server',
                            'number': len(users[rooms.index(self.room_group_name)]),
                        }
                    )
                else:
                    self.send(text_data=json.dumps({
                        'message': "Nope",
                    }))
            elif message == "/closing_screen":
                try:
                    users[rooms.index(self.room_group_name)].remove(username)
                    if len(users[rooms.index(self.room_group_name)]) == 0:
                        remove(self)
                    elif username == hosts[rooms.index(self.room_group_name)]:
                        hosts[rooms.index(self.room_group_name)] = random.choice(users[rooms.index(self.room_group_name)])
                        async_to_sync(self.channel_layer.group_send)(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'message': "?newhost",
                                'username': hosts[rooms.index(self.room_group_name)],
                            }
                        )
                except:
                    print("Goodbye")
            elif message == "?start":
                started[rooms.index(self.room_group_name)] = True
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
                    sleep(1)
                    hosts[rooms.index(self.room_group_name)] = random.choice(users[rooms.index(self.room_group_name)])
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': "?round2",
                            'username': hosts[rooms.index(self.room_group_name)],
                        }
                    )
            elif message == "?round2":
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
                        'message': message,
                        'username': username,
                    }
                )
            elif message == "?round3":
                cards[rooms.index(self.room_group_name)] = create_cards()
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': "?round3",
                        'username': "server",
                    }
                )
            elif message == "?bus":
                move = text_data_json['move']
                if len(cards[rooms.index(self.room_group_name)]) == 0:
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': "?empty",
                            'username': "server",
                        }
                    )
                else:
                    card = random.choice(cards[rooms.index(self.room_group_name)])
                    cards[rooms.index(self.room_group_name)].remove(card)
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': "?card",
                            'username': "#round3",
                            'card': card,
                            'move': move
                        }
                    )
            elif message == "?drink":
                lie = text_data_json['lie']
                card = text_data_json['card']
                looked = text_data_json['looked']
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': username,
                        'card': card,
                        'lie': lie,
                        'looked': looked
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
            elif message == "?finished":
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': username,
                    }
                )
            elif message == "?response":
                response = text_data_json['response']
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': username,
                        'response': response
                    }
                )
            elif message == "?reset":
                if len(cards[rooms.index(self.room_group_name)]) == 0:
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': "?empty",
                            'username': "server",
                        }
                    )
                else:
                    card = random.choice(cards[rooms.index(self.room_group_name)])
                    cards[rooms.index(self.room_group_name)].remove(card)
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': "?card",
                            'username': "#reset",
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

            elif message == "?left":
                left = text_data_json['left']
                cardsleft[rooms.index(self.room_group_name)].append([username, left])
                if len(cardsleft[rooms.index(self.room_group_name)]) == len(users[rooms.index(self.room_group_name)]):
                    highest = 0
                    passenger = ""
                    found = False
                    for c in cardsleft[rooms.index(self.room_group_name)]:
                        if highest < c[1]:
                            highest = c[1]
                    while not found:
                        selected = random.choice(cardsleft[rooms.index(self.room_group_name)])
                        if selected[1] == highest:
                            found = True
                            passenger = selected[0]
                    card = random.choice(cards[rooms.index(self.room_group_name)])
                    cards[rooms.index(self.room_group_name)].remove(card)
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': "?inthebus",
                            'username': passenger,
                            'card': card
                        }
                    )
            else:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': username,
                    }
                )
        except:
            print("Oeps")

    # Receive message from room group
    def chat_message(self, event):
        try:
            message = event['message']
            username = event['username']

            if message == "?round1":
                quest = event['question']
                self.send(text_data=json.dumps({
                    'message': message,
                    'username': username,
                    'question': quest
                }))
            elif message == "?response":
                response = event['response']
                self.send(text_data=json.dumps({
                    'message': message,
                    'username': username,
                    'response': response
                }))
            elif message == "?card" or message == "?placecard" or message == "?inthebus":
                card = event['card']
                if username == "#round3":
                    move = event['move']
                    self.send(text_data=json.dumps({
                        'message': message,
                        'username': username,
                        'card': card,
                        'move': move
                    }))
                else:
                    self.send(text_data=json.dumps({
                        'message': message,
                        'username': username,
                        'card': card
                    }))
            elif message == "?drink":
                lie = event['lie']
                card = event['card']
                looked = event['looked']
                self.send(text_data=json.dumps({
                    'message': message,
                    'username': username,
                    'card': card,
                    'lie': lie,
                    'looked': looked
                }))
            elif message == "?players":
                NoOfPlayers = event['number']
                self.send(text_data=json.dumps({
                    'message': message,
                    'username': username,
                    'number': NoOfPlayers
                }))
            else:
                # Send message to WebSocket
                self.send(text_data=json.dumps({
                    'message': message,
                    'username': username
                }))
        except:
            print("Oeps")



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


def remove(self):
    del users[rooms.index(self.room_group_name)]
    del question[rooms.index(self.room_group_name)]
    del user[rooms.index(self.room_group_name)]
    del cards[rooms.index(self.room_group_name)]
    del round2[rooms.index(self.room_group_name)]
    del hosts[rooms.index(self.room_group_name)]
    del cardsleft[rooms.index(self.room_group_name)]
    rooms.remove(self.room_group_name)


def create_cards():
    deck = []
    for s in colors:
        for i in range(2, 15):
            deck.append(s + str(i))
    return deck
