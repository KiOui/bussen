import secrets

from pyCardDeck import Deck, BaseCard

import bussen.models
import json
import math


class BusCard(BaseCard):
    """BusCard class."""

    def __init__(self, suit: str, rank: str, closed: bool = False, owner=None, random_id: str = None):
        """
        Initialize a BusCard object.

        :param suit: the suit
        :param rank: the rank
        :param closed: whether or not this card is closed
        :param owner: the owner (Player) of this card
        :param random_id: a random identifier for this card
        """
        super().__init__(f"{suit} {rank}")
        self.suit = suit
        self.rank = rank
        self.closed = True if closed else False
        self.owner = owner
        self.random_id = random_id

    def __eq__(self, other):
        """Check if a BusCard is equal to this BusCard."""
        return self.suit == other.suit and self.rank == other.rank

    def __lt__(self, other):
        """Check if a BusCard is less than this BusCard."""
        return self.to_int() < other.to_int()

    def to_int(self):
        """Convert a card rank to an Integer."""
        if self.rank == "J":
            return 11
        elif self.rank == "Q":
            return 12
        elif self.rank == "K":
            return 13
        elif self.rank == "A":
            return 14
        else:
            return int(self.rank)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "suit": self.suit,
            "rank": self.rank,
            "closed": self.closed,
            "owner": self.owner.id if self.owner is not None else None,
            "random_id": self.random_id,
        }

    @staticmethod
    def from_dict(dictionary: dict):
        """Import from dictionary."""
        return BusCard(
            dictionary["suit"],
            dictionary["rank"],
            closed=dictionary["closed"],
            owner=bussen.models.Player.objects.get(id=dictionary["owner"])
            if dictionary["owner"] is not None and bussen.models.Player.objects.filter(id=dictionary["owner"]).exists()
            else None,
            random_id=dictionary["random_id"],
        )

    def to_json(self):
        """Convert to json."""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str):
        """Import from json."""
        dictionary = json.loads(json_str)
        return BusCard.from_dict(dictionary)

    @staticmethod
    def create_random_card_id():
        """Create a random identifier (32 characters)."""
        return secrets.token_hex(32)

    def copy(self):
        """Copy this object."""
        return BusCard(self.suit, self.rank, closed=self.closed, owner=self.owner, random_id=self.random_id)


class Pyramid:
    """Bus Pyramid class."""

    def __init__(self, preset: [[BusCard]] = None, cards_on_pyramid: [BusCard] = None, current_card_index: int = None):
        """
        Initialize the Pyramid.

        :param preset: a list of lists of BusCards
        :param cards_on_pyramid: a list of BusCards indicating the cards on the pyramid
        :param current_card_index: the current active pyramid card index
        """
        self.current_card_index = current_card_index
        if cards_on_pyramid is None:
            self.cards_on_pyramid = list()
        else:
            self.cards_on_pyramid = cards_on_pyramid
        if preset is None:
            self.pyramid = list()
        else:
            self.pyramid = preset

    def construct(self, layers: [int], deck: Deck):
        """Construct a new Pyramid."""
        cards_needed = sum(layers)
        if len(list(deck)) < cards_needed:
            raise ValueError("There are not enough cards in the deck to build a pyramid")
        self.pyramid = list()
        for layer in layers:
            new_layer = list()
            for _ in range(0, layer):
                new_card = deck.draw()
                new_card.closed = True
                new_layer.append(new_card)
            self.pyramid.append(new_layer)
        if cards_needed > 0:
            self.current_card_index = cards_needed
        else:
            self.current_card_index = None

    def set_next_pyramid_card(self):
        """Set next pyramid card as active."""
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.current_card().closed = False
            self.cards_on_pyramid = []
            return True
        else:
            self.current_card_index = None
            return False

    def current_card(self):
        """Get the current active pyramid card."""
        flattened_pyramid = [x for row in self.pyramid for x in row]
        if self.current_card_index is not None and 0 <= self.current_card_index < len(flattened_pyramid):
            return flattened_pyramid[self.current_card_index]
        else:
            return None

    def add_card_to_pyramid(self, card: BusCard):
        """Add a card to the pyramid card list."""
        copy = card.copy()
        copy.random_id = BusCard.create_random_card_id()
        self.cards_on_pyramid.append(copy)

    def id_in_cards_list(self, random_id: str) -> bool:
        """Check if a random identifier of a BusCard is in the pyramid card list."""
        if random_id is None:
            return False
        for card in self.cards_on_pyramid:
            if card.random_id == random_id:
                return True
        return False

    def owner_of_id(self, random_id: str):
        """Get the owner of a random identifier of a BusCard in the pyramid card list."""
        if random_id is None:
            return None

        for card in self.cards_on_pyramid:
            if card.random_id == random_id:
                return card.owner
        return None

    def remove_card_in_pyramid_list(self, random_id: str):
        """Remove a card with a random identifier from the pyramid card list."""
        for i in range(0, len(self.cards_on_pyramid)):
            if self.cards_on_pyramid[i].random_id == random_id:
                if self.current_card() is not None and self.cards_on_pyramid[i].rank == self.current_card().rank:
                    return None
                else:
                    card = self.cards_on_pyramid[i]
                    del self.cards_on_pyramid[i]
                    return card
        return None

    def copy(self):
        """Copy this object."""
        pyramid_copy = list()
        for row in self.pyramid:
            layer_copy = list()
            for card in row:
                layer_copy.append(card.copy())
            pyramid_copy.append(layer_copy)

        cards_on_pyramid_copy = list()
        for card in self.cards_on_pyramid:
            cards_on_pyramid_copy.append(card.copy())

        return Pyramid(
            preset=pyramid_copy, current_card_index=self.current_card_index, cards_on_pyramid=cards_on_pyramid_copy
        )

    def to_dict(self):
        """Convert to dictionary."""
        list_pyramid = list()
        for layer in self.pyramid:
            new_layer = list()
            for card in layer:
                new_layer.append(card.to_dict())
            list_pyramid.append(new_layer)
        return {
            "pyramid": list_pyramid,
            "current_card_index": self.current_card_index,
            "cards_on_pyramid": [x.to_dict() for x in self.cards_on_pyramid],
        }

    @staticmethod
    def from_dict(dictionary):
        """Import from dictionary."""
        list_pyramid = list()
        for layer in dictionary["pyramid"]:
            new_layer = list()
            for card in layer:
                new_layer.append(BusCard.from_dict(card))
            list_pyramid.append(new_layer)
        return Pyramid(
            preset=list_pyramid,
            cards_on_pyramid=[BusCard.from_dict(x) for x in dictionary["cards_on_pyramid"]],
            current_card_index=dictionary["current_card_index"],
        )

    def to_json(self):
        """Convert to json."""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str):
        """Import from json."""
        dictionary = json.loads(json_str)
        return Pyramid.from_dict(dictionary)

    def __str__(self):
        """Convert to string."""
        return str(self.to_dict())


class Bus:
    """Bus class."""

    def __init__(self, preset: [BusCard] = None, current_card_index: int = 0):
        """
        Initialize a Bus.

        :param preset: a list of BusCards indicating the cards on the bus
        :param current_card_index: the index the bus is at in the preset list
        """
        self.current_card_index = current_card_index
        if preset is None:
            self.bus = list()
        else:
            self.bus = preset

    def construct(self, amount, deck: Deck):
        """Construct a Bus."""
        if deck.cards_left < amount:
            raise ValueError("There are not enough cards in the deck to construct a bus")

        self.bus = list()
        for _ in range(0, amount):
            card = deck.draw()
            card.closed = True
            self.bus.append(card)
        self.current_card_index = 0

    def guess_card(self, guess: str, card: BusCard):
        """Guess a card in the Bus."""
        current_card = self.current_card()
        if guess == "higher":
            correct = current_card < card
        elif guess == "lower":
            correct = current_card > card
        else:
            correct = current_card == card

        self.bus[self.current_card_index] = card

        if correct:
            self.current_card_index += 1
        else:
            self.current_card_index = 0

        return correct

    def current_card(self):
        """Get the current BusCard."""
        if 0 <= self.current_card_index < len(self.bus):
            return self.bus[self.current_card_index]
        else:
            return None

    def to_dict(self):
        """Convert to dictionary."""
        return {"bus": [x.to_dict() for x in self.bus], "current_card_index": self.current_card_index}

    @staticmethod
    def from_dict(dictionary):
        """Import from dictionary."""
        return Bus(
            preset=[BusCard.from_dict(x) for x in dictionary["bus"]],
            current_card_index=dictionary["current_card_index"],
        )

    def to_json(self):
        """Convert to json."""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str):
        """Import from json."""
        dictionary = json.loads(json_str)
        return Pyramid.from_dict(dictionary)


class BusGame:
    """BusGame class."""

    HEARTS = "Hearts"
    SPADES = "Spades"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"

    PYRAMID_SIZE = [1, 2, 3, 4, 5]
    PYRAMID_SIZE_CARDS = sum(PYRAMID_SIZE)
    MAXIMUM_AMOUNT_OF_PLAYERS = math.floor((52 - PYRAMID_SIZE_CARDS) / 4)

    BUS_CARD_AMOUNT = 6

    RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

    VALUE_RED = 0
    VALUE_BLACK = 1

    VALUE_HIGHER = 0
    VALUE_LOWER = 1
    VALUE_SAME = 2

    VALUE_BETWEEN = 0
    VALUE_OUTSIDE = 1

    VALUE_HAVE_SUIT = 0
    VALUE_DO_NOT_HAVE_SUIT = 1

    def __init__(self, deck: Deck = None, pyramid: Pyramid = None, bus: Bus = None):
        """
        Initialize a BusGame object.

        :param deck: the deck to use
        :param pyramid: the pyramid to use
        :param bus: the bus to use
        """
        if deck is None:
            self.deck = Deck(cards=BusGame.generate_deck(), reshuffle=False)
            self.deck.shuffle()
        else:
            self.deck = deck
        self.pyramid = Pyramid() if pyramid is None else pyramid
        self.bus = Bus() if bus is None else bus

    @staticmethod
    def generate_deck():
        """
        Generate a deck of cards.

        :return: List with all 52 poker playing cards
        """
        suits = [BusGame.HEARTS, BusGame.DIAMONDS, BusGame.CLUBS, BusGame.SPADES]
        cards = list()
        for suit in suits:
            for rank in BusGame.RANKS:
                cards.append(BusCard(suit, rank))
        return cards

    @property
    def cards_left(self):
        """Get the amount of cards left in the deck."""
        return self.deck.cards_left

    def draw_card(self):
        """Draw a card from the deck."""
        return self.deck.draw()

    def reset_deck(self, shuffle=True):
        """Reset the deck."""
        self.deck = Deck(cards=BusGame.generate_deck(), reshuffle=False)
        if shuffle:
            self.deck.shuffle()

    def set_pyramid(self):
        """Reset the pyramid."""
        self.pyramid.construct(self.PYRAMID_SIZE, self.deck)

    def set_bus(self):
        """Reset the bus."""
        self.bus.construct(self.BUS_CARD_AMOUNT, self.deck)

    @staticmethod
    def get_question_round_question(question_number):
        """Get a question for phase 1."""
        if question_number == 0:
            return {
                "question": "Red or black?",
                "answers": [
                    {"answer": "Red", "value": BusGame.VALUE_RED},
                    {"answer": "Black", "value": BusGame.VALUE_BLACK},
                ],
            }
        elif question_number == 1:
            return {
                "question": "Higher lower or the same?",
                "answers": [
                    {"answer": "Higher", "value": BusGame.VALUE_HIGHER},
                    {"answer": "Lower", "value": BusGame.VALUE_LOWER},
                    {"answer": "The same", "value": BusGame.VALUE_SAME},
                ],
            }
        elif question_number == 2:
            return {
                "question": "Between the rank of the current cards or outside of them?",
                "answers": [
                    {"answer": "In between", "value": BusGame.VALUE_BETWEEN},
                    {"answer": "Outside", "value": BusGame.VALUE_OUTSIDE},
                    {"answer": "The same", "value": BusGame.VALUE_SAME},
                ],
            }
        elif question_number == 3:
            return {
                "question": "Do you have the next suit or not?",
                "answers": [
                    {"answer": "I have the suit already", "value": BusGame.VALUE_HAVE_SUIT},
                    {"answer": "I don't have the suit", "value": BusGame.VALUE_DO_NOT_HAVE_SUIT},
                    {"answer": "Rainbow", "value": BusGame.VALUE_SAME},
                ],
            }
        else:
            raise ValueError(f"There is no question for question round {question_number}")

    @staticmethod
    def get_question_round_question_1_outcome(value: int, card: BusCard):
        """Get the question evaluation for question 1."""
        if value == BusGame.VALUE_RED:
            return card.suit == BusGame.DIAMONDS or card.suit == BusGame.HEARTS
        else:
            return card.suit == BusGame.SPADES or card.suit == BusGame.CLUBS

    @staticmethod
    def get_question_round_question_2_outcome(value: int, current_card: BusCard, drawn_card: BusCard):
        """Get the question evaluation for question 2."""
        if value == BusGame.VALUE_HIGHER:
            return drawn_card > current_card
        elif value == BusGame.VALUE_LOWER:
            return drawn_card < current_card
        else:
            return drawn_card == current_card

    @staticmethod
    def get_question_round_question_3_outcome(
        value: int, first_card: BusCard, second_card: BusCard, drawn_card: BusCard
    ):
        """Get the question evaluation for question 3."""
        if value == BusGame.VALUE_BETWEEN:
            return first_card > drawn_card > second_card or first_card < drawn_card < second_card
        elif value == BusGame.VALUE_OUTSIDE:
            return not (first_card > drawn_card > second_card or first_card < drawn_card < second_card)
        else:
            return first_card.rank == drawn_card.rank or second_card.rank == drawn_card.rank

    @staticmethod
    def get_question_round_question_4_outcome(value: int, cards: [BusCard], drawn_card: BusCard):
        """Get the question evaluation for question 4."""
        if value == BusGame.VALUE_HAVE_SUIT:
            return drawn_card.suit in [x.suit for x in cards]
        elif value == BusGame.VALUE_DO_NOT_HAVE_SUIT:
            return drawn_card.suit not in [x.suit for x in cards]
        else:
            return drawn_card.rank in [x.rank for x in cards]

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "deck": [x.to_dict() for x in list(self.deck)],
            "pyramid": self.pyramid.to_dict(),
            "bus": self.bus.to_dict(),
        }

    @staticmethod
    def from_dict(dictionary):
        """Import from dictionary."""
        return BusGame(
            deck=Deck(cards=[BusCard.from_dict(x) for x in dictionary["deck"]], reshuffle=False),
            pyramid=Pyramid.from_dict(dictionary["pyramid"]),
            bus=Bus.from_dict(dictionary["bus"]),
        )

    def to_json(self):
        """Convert to json."""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str):
        """Import from json."""
        dictionary = json.loads(json_str)
        return BusGame.from_dict(dictionary)


class BusHand:
    """BusHand class."""

    MAX_CARDS_IN_HAND = 4

    def __init__(self, preset=None):
        """Initialize BusHand object."""
        self.hand = list() if preset is None else preset

    def add_card(self, card):
        """Add a card to the bus hand."""
        if len(self.hand) > 3:
            return False
        else:
            self.hand.append(card)
            return True

    def remove_card(self, card):
        """Remove a card from the bus hand."""
        if card in self.hand:
            self.hand.remove(card)
            return True
        else:
            return False

    def copy(self):
        """Copy this object."""
        return BusHand(preset=[x.copy() for x in self.hand])

    def to_dict(self):
        """Convert to dictionary."""
        return {"hand": [x.to_dict() for x in self.hand]}

    @staticmethod
    def from_dict(dictionary):
        """Import from dictionary."""
        return BusHand(preset=[BusCard.from_dict(x) for x in dictionary["hand"]])

    def to_json(self):
        """Convert to json."""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str):
        """Import from json."""
        dictionary = json.loads(json_str)
        return BusHand.from_dict(dictionary)


def get_player_from_request(request):
    """
    Get a player from a request.

    :param request: the request
    :return: a Player object if the request has a player, False otherwise
    """
    player_id = request.COOKIES.get(bussen.models.Player.PLAYER_COOKIE_NAME, None)
    return get_player_from_cookie(player_id)


def get_player_from_cookie(player_id: str):
    """
    Get a player from the player id.

    :param player_id: the player id
    :return: a Player object if the player id matches, None otherwise
    """
    if player_id is not None:
        try:
            player = bussen.models.Player.objects.get(cookie=player_id)
            return player
        except bussen.models.Player.DoesNotExist:
            return None

    return None


def decode_message(message):
    """Decode a message from json."""
    text = message.get("text", None)
    if text is not None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}
    else:
        return {}
