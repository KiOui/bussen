import secrets
from typing import List
import json

import pyCardDeck
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from pyCardDeck import CardNotFound, NoCards, PokerCard
from rooms.services import card_rank_to_int
from django.core.validators import MaxValueValidator, MinValueValidator
import math

from pyCardDeck.deck import Deck


class GameStateException(Exception):
    """Game state exception."""

    pass


class Game(models.Model):
    """Game model."""

    PYRAMID_SIZE = [1, 2, 3, 4, 5]
    PYRAMID_SIZE_CARDS = sum(PYRAMID_SIZE)
    MAXIMUM_AMOUNT_OF_PLAYERS = math.floor((52 - PYRAMID_SIZE_CARDS) / 4)

    PHASE_OPEN = 0
    PHASE_1 = 1
    PHASE_2 = 2
    PHASE_3 = 3

    HEARTS = "Hearts"
    SPADES = "Spades"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"

    PHASES = ((PHASE_OPEN, "Open for participants"), (PHASE_1, "Phase 1"), (PHASE_2, "Phase 2"), (PHASE_3, "Phase 3"))

    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    state = models.TextField()
    phase = models.IntegerField(choices=PHASES, default=0, null=False, blank=False)
    current_player = models.IntegerField(null=True, blank=False)
    slug = models.SlugField(null=False, blank=False, unique=True, max_length=256)
    pyramid = models.TextField(default="[]")
    cards_on_pyramid = models.TextField(default="[]")
    current_card = models.IntegerField(
        null=True, blank=False, validators=[MaxValueValidator(PYRAMID_SIZE_CARDS), MinValueValidator(0)]
    )

    def __str__(self):
        """
        Convert this object to string.

        :return: a string with the name of the game
        """
        return self.name

    @staticmethod
    def generate_deck() -> List[PokerCard]:
        """
        Generate a deck of cards.

        :return: List with all 52 poker playing cards
        """
        suits = [Game.HEARTS, Game.DIAMONDS, Game.CLUBS, Game.SPADES]
        ranks = {
            "A": "A",
            "2": "2",
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7",
            "8": "8",
            "9": "9",
            "10": "10",
            "J": "J",
            "Q": "Q",
            "K": "K",
        }
        cards = []
        for suit in suits:
            for rank, name in ranks.items():
                cards.append(PokerCard(suit, rank, name))
        return cards

    def save(self, *args, **kwargs):
        """
        Save method for Game object.

        Creates a slug for the game
        :param args: arguments
        :param kwargs: keyword arguments
        :return: None
        """
        if self.slug is None or self.slug == "":
            new_slug = slugify(self.name)
            if Game.objects.filter(slug=new_slug).exists():
                return ValueError("A slug for this game already exists, please choose another name")
            self.slug = new_slug
        super(Game, self).save(*args, **kwargs)

    def get_card(self):
        """
        Get a card from the deck.

        :return: a card from the deck
        """
        current_deck = Deck()
        current_deck.load(self.state)
        card = current_deck.draw()
        self.state = current_deck.export("JSON")
        self.save()
        return card

    def reset_deck(self):
        """
        Reset the card deck to the default deck.

        :return: None
        """
        default_deck = Deck(cards=self.generate_deck(), reshuffle=False)
        default_deck.shuffle()
        self.state = default_deck.export("JSON")
        self.save()

    def start_phase_1(self):
        """
        Start Phase 1 of the game.

        :return: True if Phase 1 has been started or was already running, False otherwise
        """
        if self.phase == self.PHASE_1:
            return True
        elif self.phase != self.PHASE_OPEN or not self.enough_players:
            return False

        self.phase = self.PHASE_1
        self.save()

        self.reset_deck()
        for player in self.ordered_players:
            player.new_hand()

        self.current_player = 0
        self.save()
        return True

    def start_phase_2(self):
        """
        Start Phase 2 of the game.

        :return: True if Phase 2 has been started or was already running, False otherwise
        """
        if self.phase == self.PHASE_2:
            return True
        elif self.phase != self.PHASE_1:
            return False

        self.phase = self.PHASE_2
        self.save()

        self.current_player = None
        self.initialise_pyramid(save=False)
        self.save()
        return True

    def initialise_pyramid(self, save=True):
        """
        Initialise the pyramid for phase 2.

        :param save: whether or not to save after initialization
        :return: None
        """
        pyramid = list()
        for amount_of_cards in self.PYRAMID_SIZE:
            pyramid_row = list()
            for _ in range(0, amount_of_cards):
                new_card = self.get_card()
                pyramid_row.append({"suit": new_card.suit, "rank": new_card.rank})
            pyramid.append(pyramid_row)
        self.pyramid = json.dumps(pyramid)
        if save:
            self.save()

    @property
    def ordered_players(self):
        """
        Get ordered players for this game.

        :return: a list of players ordered by cookie value
        """
        return Player.objects.filter(current_game=self).order_by("cookie")

    @property
    def enough_players(self):
        """
        Check if the game has enough online players to start.

        :return: True if there are more than 1 online player in this game
        """
        return self.ordered_players.count() > 1

    @property
    def amount_of_players(self):
        """
        Get the amount of players in the Game.

        :return: the amount of players in this game
        """
        return self.ordered_players.count()

    @property
    def amount_of_online_players(self):
        """
        Get the amount of online players in the Game.

        :return: the amount of online players in the game
        """
        return self.ordered_players.filter(online=True).count()

    def get_amount_of_players(self):
        """
        Get the amount of players for this game.

        :return: the amount of players in this game
        """
        return self.ordered_players.count()

    def get_amount_of_online_players(self):
        """
        Get the amount of online players in the Game.

        :return: the amount of online players in the game
        """
        return self.ordered_players.filter(online=True).count()

    def to_json(self):
        """
        Convert this object to a json string.

        :return: a string containing a json representation of this Game
        """
        return json.dumps(self.to_dict())

    def to_dict(self):
        """
        Convert this object to a dictionary.

        :return: a dictionary containing relevant parameters of this Game
        """
        return {
            "phase": self.phase,
            "current_player": self.current_player,
            "players": [x.to_json() for x in self.ordered_players],
        }

    @property
    def current_player_obj(self):
        """
        Get the current Player in this Game.

        :return: None if there is no current player, the Player object of the current player otherwise
        """
        if self.current_player is not None:
            return self.ordered_players[self.current_player]
        else:
            return None

    def get_card_question(self, player):
        """
        Get a card question.

        :param player: the Player to get a card question for
        :return: a dictionary with a 'question' attribute indicating the question and a 'answers' attribute indicating
        all possible answers in a list, returns False if the player is not a player of this game or if the player
        has more than four cards.
        """
        if player not in self.ordered_players:
            return False

        if len(player.current_hand.to_list()) == 0:
            return {
                "question": "Red or black?",
                "answers": [{"answer": "Red", "value": 0}, {"answer": "Black", "value": 1}],
            }
        elif len(player.current_hand.to_list()) == 1:
            return {
                "question": "Higher lower or the same?",
                "answers": [
                    {"answer": "Higher", "value": 0},
                    {"answer": "Lower", "value": 1},
                    {"answer": "The same", "value": 2},
                ],
            }
        elif len(player.current_hand.to_list()) == 2:
            return {
                "question": "Between the rank of the current cards or outside of them?",
                "answers": [
                    {"answer": "In between", "value": 0},
                    {"answer": "Outside", "value": 1},
                    {"answer": "The same", "value": 2},
                ],
            }
        elif len(player.current_hand.to_list()) == 3:
            return {
                "question": "Do you have the next suit or not?",
                "answers": [
                    {"answer": "I have the suit already", "value": 0},
                    {"answer": "I don't have the suit", "value": 1},
                    {"answer": "Rainbow", "value": 2},
                ],
            }
        else:
            return False

    def phase1_next_turn(self):
        """
        Rotate the turn variable in this class to indicate a next Player.

        Also starts phase 2 if necessary
        :return: None
        """
        least_cards = Hand.MAX_CARDS_IN_HAND
        player_turn = self.current_player
        for i in range(0, len(self.ordered_players)):
            if len(self.ordered_players[i].current_hand.to_list()) < least_cards:
                least_cards = len(self.ordered_players[i].current_hand.to_list())
                player_turn = i
        if least_cards == Hand.MAX_CARDS_IN_HAND:
            self.start_phase_2()
        else:
            self.current_player = player_turn
            self.save()

    def handle_phase1_first_question(self, player, value):
        """Handle first question of phase 1."""
        card = self.get_card()
        player.current_hand.add_card_to_hand(card)
        if value == 0:
            # Red
            return card.suit == self.DIAMONDS or card.suit == self.HEARTS, False
        else:
            # Black
            return card.suit == self.SPADES or card.suit == self.CLUBS, False

    def handle_phase1_second_question(self, player, value):
        """Handle second question of phase 1."""
        card = self.get_card()
        drawn_card_rank = card_rank_to_int(card.rank)
        current_card_rank = card_rank_to_int(player.current_hand.to_list()[0]["rank"])
        player.current_hand.add_card_to_hand(card)
        if value == 0:
            # Higher
            return current_card_rank < drawn_card_rank, False
        elif value == 1:
            # Lower
            return current_card_rank > drawn_card_rank, False
        else:
            # The same
            return current_card_rank == drawn_card_rank, True

    def handle_phase1_third_question(self, player, value):
        """Handle third question of phase 1."""
        card = self.get_card()
        drawn_card_rank = card_rank_to_int(card.rank)
        first_card_rank = card_rank_to_int(player.current_hand.to_list()[0]["rank"])
        second_card_rank = card_rank_to_int(player.current_hand.to_list()[1]["rank"])
        player.current_hand.add_card_to_hand(card)
        if value == 0:
            # In between
            return (
                first_card_rank > drawn_card_rank > second_card_rank
                or first_card_rank < drawn_card_rank < second_card_rank,
                False,
            )
        elif value == 1:
            # Outside
            return (
                not (
                    first_card_rank > drawn_card_rank > second_card_rank
                    or first_card_rank < drawn_card_rank < second_card_rank
                ),
                False,
            )
        else:
            # The same
            return first_card_rank == drawn_card_rank or second_card_rank == drawn_card_rank, True

    def handle_phase1_fourth_question(self, player, value):
        """Handle fourth question of phase 1."""
        card = self.get_card()
        drawn_card_suit = card.suit
        first_card_suit = player.current_hand.to_list()[0]["suit"]
        second_card_suit = player.current_hand.to_list()[1]["suit"]
        third_card_suit = player.current_hand.to_list()[2]["suit"]
        suits = [first_card_suit, second_card_suit, third_card_suit]
        player.current_hand.add_card_to_hand(card)
        if value == 0:
            # Has suit
            return drawn_card_suit in suits, False
        elif value == 1:
            # Does not have suit
            return drawn_card_suit not in suits, False
        else:
            # Rainbow
            suits.append(drawn_card_suit)
            return len(set(suits)) == 4, True

    def handle_phase1_answer(self, player, value):
        """Handle a phase 1 answer."""
        if player not in self.ordered_players and player is self.current_player_obj:
            return None

        if len(player.current_hand.to_list()) == 0:
            correct, group_drink = self.handle_phase1_first_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        elif len(player.current_hand.to_list()) == 1:
            correct, group_drink = self.handle_phase1_second_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        elif len(player.current_hand.to_list()) == 2:
            correct, group_drink = self.handle_phase1_third_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        elif len(player.current_hand.to_list()) == 3:
            correct, group_drink = self.handle_phase1_fourth_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        else:
            return None

    @property
    def pyramid_list(self):
        """
        Get the pyramid as a list with "closed" and "pile" dictionary keys.

        :return: the pyramid list with "closed" and "pile" dictionary keys indicating wheter a card is closed or the
        current pile card
        """
        pyramid_list = json.loads(self.pyramid)
        closed_cards = self.PYRAMID_SIZE_CARDS - (self.current_card + 1 if self.current_card is not None else 0)
        for pyramid_row in pyramid_list:
            for card in pyramid_row:
                if closed_cards > 0:
                    card["closed"] = True
                    card["pile"] = False
                    closed_cards -= 1
                elif closed_cards == 0:
                    card["closed"] = False
                    card["pile"] = True
                    closed_cards -= 1
                else:
                    card["closed"] = False
                    card["pile"] = False

        return pyramid_list

    @property
    def current_pyramid_card(self):
        """Get the current pyramid card."""
        pyramid_list = json.loads(self.pyramid)
        closed_cards = self.PYRAMID_SIZE_CARDS - (self.current_card + 1 if self.current_card is not None else 0)
        for pyramid_row in pyramid_list:
            for card in pyramid_row:
                if closed_cards == 0:
                    return card
                closed_cards -= 1
        return None

    def set_next_pyramid_card(self):
        """Iterate the pyramid to the next card."""
        if self.phase == Game.PHASE_2:
            if self.current_card is None:
                self.current_card = 0
                self.reset_cards_on_pyramid(save=False)
                self.save()
            elif self.current_card == Game.PYRAMID_SIZE_CARDS - 1:
                # TODO: Move to phase 3
                pass
            else:
                self.current_card += 1
                self.reset_cards_on_pyramid(save=False)
                self.save()

        return False

    @property
    def cards_on_pyramid_list_player_ids(self):
        """Get cards on the pyramid as a list with players as Player objects."""
        cards_on_pyramid = self.cards_on_pyramid_list
        for card in cards_on_pyramid:
            card["player"] = (
                Player.objects.get(id=card["player"]) if Player.objects.filter(id=card["player"]).exists() else None
            )
        return cards_on_pyramid

    @property
    def cards_on_pyramid_list(self):
        """Get cards on the pyramid as a list with players as Player ids."""
        return json.loads(self.cards_on_pyramid)

    def reset_cards_on_pyramid(self, save=True):
        """Reset cards on the pyramid."""
        self.cards_on_pyramid = "[]"
        if save:
            self.save()

    def add_card_on_pyramid(self, suit, rank, player):
        """Add a card to the pyramid list."""
        cards_on_pyramid = self.cards_on_pyramid_list
        cards_on_pyramid.append({"player": player.id, "suit": suit, "rank": rank, "random_id": secrets.token_hex(32)})
        self.cards_on_pyramid = json.dumps(cards_on_pyramid)
        self.save()

    def add_card_to_pile(self, player, suit, rank):
        """Add a card to the pyramid card pile while first checking if it can be removed from the player."""
        if player not in self.ordered_players:
            return False

        if player.current_hand.remove_card_from_hand(pyCardDeck.PokerCard(suit=suit, rank=rank, name=rank)):
            self.add_card_on_pyramid(suit, rank, player)
            return True
        else:
            return False

    def id_in_pyramid(self, id):
        """Check if an id of a card is in the pyramid list."""
        for i in range(0, len(self.cards_on_pyramid_list)):
            if self.cards_on_pyramid_list[i]["random_id"] == id:
                return i
        return False

    def remove_position_from_pyramid(self, position):
        """Remove a position from the pyramid."""
        pyramid_list = self.cards_on_pyramid_list
        del pyramid_list[position]
        self.cards_on_pyramid = json.dumps(pyramid_list)
        self.save()

    def call_card(self, id):
        """Call a card with a specific id."""
        position = self.id_in_pyramid(id)
        current_pyramid_card = self.current_pyramid_card
        if position is not False and current_pyramid_card is not None:
            card = self.cards_on_pyramid_list_player_ids[position]
            if card["rank"] == current_pyramid_card["rank"]:
                return False, card["player"]
            else:
                self.remove_position_from_pyramid(position)
                if card["player"] is not None:
                    card["player"].current_hand.add_card_to_hand(
                        PokerCard(suit=card["suit"], rank=card["rank"], name=card["rank"])
                    )
                    return True, card["player"]
                return True, None
        return False, None


class Hand(models.Model):
    """Hand model."""

    MAX_CARDS_IN_HAND = 4

    hand = models.TextField()

    @property
    def current_hand(self):
        """Get the current hand as a Deck object."""
        try:
            current_hand = Deck()
            current_hand.load(self.hand)
            return current_hand
        except pyCardDeck.errors.UnknownFormat:
            return Deck(reshuffle=False)

    def add_card_to_hand(self, card):
        """
        Add a card to this hand.

        :param card: the card to add
        :return: None
        """
        if len(self.to_list()) >= self.MAX_CARDS_IN_HAND:
            return False
        current_hand = self.current_hand
        current_hand.add_single(card, position=0)
        self.hand = current_hand.export("JSON")
        self.save()
        return True

    @property
    def card_list(self):
        """Get the current hand as a List while appending empty cards if list length is smaller than 4."""
        open_cards = self.to_list()[:4]
        while len(open_cards) < 4:
            open_cards.append({"suit": None, "rank": None})
        return open_cards

    @property
    def no_empty_card_list(self):
        """Get the current hand as List."""
        open_cards = self.to_list()
        return open_cards

    def remove_card_from_hand(self, card):
        """
        Remove a card from this hand.

        :param card: the card to remove
        :return: True if the card could be removed, False otherwise
        """
        current_hand = self.current_hand
        try:
            current_hand.draw_specific(card)
        except CardNotFound:
            return False
        except NoCards:
            return False
        self.hand = current_hand.export("JSON")
        self.save()
        return True

    def to_json(self):
        """Convert this object to json."""
        return json.dumps(self.to_list())

    def to_list(self):
        """Convert this object to a List."""
        current_hand = self.current_hand
        list_obj = [{"suit": x.suit, "rank": x.rank} for x in current_hand]
        list_obj.reverse()
        return list_obj


class Player(models.Model):
    """Player model."""

    PLAYER_COOKIE_NAME = "player_id"

    cookie = models.CharField(max_length=32)
    name = models.CharField(max_length=32, blank=False, null=False)
    current_game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, default=None)
    online = models.BooleanField(default=True)
    current_hand = models.ForeignKey(Hand, on_delete=models.SET_NULL, null=True, default=None)
    last_interaction = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Convert this object to a string."""
        return self.name

    def set_online(self):
        """Set this player online."""
        self.interaction(save=False)
        self.online = True
        self.save()

    def set_offline(self):
        """Set this player offline."""
        self.interaction(save=False)
        self.online = False
        self.save()

    def new_hand(self):
        """Give this player a new hand."""
        self.current_hand = Hand.objects.create()
        self.save()

    def in_game(self):
        """
        Check if a player is in game.

        :return: the current game if a player is in game, False otherwise
        """
        if self.current_game is not None:
            return self.current_game
        else:
            return False

    def interaction(self, save=True):
        """Update last interaction of player."""
        self.last_interaction = timezone.now()
        if save:
            self.save()

    def save(self, *args, **kwargs):
        """
        Save method for Player class.

        Checks if a player can be added to a game, or if there are already enough players for a game
        :param args: arguments
        :param kwargs: keyword arguments
        :return: None
        """
        if self.current_game is not None:
            if self not in Player.objects.filter(current_game=self.current_game):
                # If we add the player to a game
                if self.current_game.amount_of_players >= Game.MAXIMUM_AMOUNT_OF_PLAYERS:
                    raise ValueError(
                        "The maximum amount of players is already reached for game {}".format(self.current_game)
                    )
        super(Player, self).save(*args, **kwargs)

    def to_json(self):
        """Convert this object to json."""
        return json.dumps(self.to_dict())

    def to_dict(self):
        """Convert this object to dict."""
        return {
            "name": self.name,
            "online": self.online,
            "last_interaction": self.last_interaction.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

    @staticmethod
    def get_new_player(name, current_game=None):
        """
        Generate a new player object with a random cookie token.

        :param name: the name for the player
        :param current_game: the current game the player is playing in (default: None)
        :return: a new Player object
        """
        random_token = secrets.token_hex(32)
        player = Player.objects.create(cookie=random_token, name=name, current_game=current_game)
        return player

    @property
    def current_question(self):
        """Get the current question for this player."""
        return self.get_card_question()

    def get_card_question(self):
        """Get the current question for this player if the player is in a game."""
        if self.current_game is not None:
            return self.current_game.get_card_question(self)

        return False
