import secrets
import json
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from bussen.services import BusGame, BusHand, BusCard


class GameStateException(Exception):
    """Game state exception."""

    pass


class BusGameModel(models.Model):
    """Game model."""

    PHASE_OPEN = 0
    PHASE_1 = 1
    PHASE_2 = 2
    PHASE_3 = 3
    PHASE_FINISHED = 4

    PHASES = (
        (PHASE_OPEN, "Open for participants"),
        (PHASE_1, "Phase 1"),
        (PHASE_2, "Phase 2"),
        (PHASE_3, "Phase 3"),
        (PHASE_FINISHED, "Finished"),
    )

    name = models.CharField(max_length=128, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    state = models.TextField(null=True, default=None)
    phase = models.IntegerField(choices=PHASES, default=0, null=False, blank=False)
    current_player_index = models.IntegerField(null=True, blank=False)
    slug = models.SlugField(null=False, blank=False, unique=True, max_length=256)

    def __init__(self, *args, **kwargs):
        """
        Initialize BusGameModel object.

        This initializes the _game property that holds the BusGame object. _original_state will also be initialized as
        a way to see whether the game state was manually changed in the save method.
        :param args: arguments
        :param kwargs: keyword arguments
        """
        super().__init__(*args, **kwargs)
        if self.state is None:
            self._game = BusGame()
        else:
            self._game = BusGame.from_json(self.state)

        self._original_state = self.state

    def __str__(self):
        """
        Convert this object to string.

        :return: a string with the name of the game
        """
        return self.name

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
            if BusGameModel.objects.filter(slug=new_slug).exists():
                return ValueError("A slug for this game already exists, please choose another name")
            self.slug = new_slug

        # Check if changes have been done to the state itself
        if self._original_state == self.state:
            self.state = self._game.to_json()
            self._original_state = self.state
        super(BusGameModel, self).save(*args, **kwargs)

    @property
    def game(self) -> BusGame:
        """Get the current BusGame object."""
        return self._game

    def get_card(self, save=True) -> BusCard:
        """
        Get a card from the deck.

        :return: a card from the deck
        """
        card = self.game.draw_card()
        if save:
            self.save()
        return card

    @property
    def cards_left(self) -> int:
        """Check if cards are left in the deck."""
        return self.game.cards_left

    def start_phase_1(self):
        """
        Start Phase 1 of the game.

        :return: True if Phase 1 has been started or was already running, False otherwise
        """
        if self.phase == self.PHASE_1:
            return True
        elif self.phase != self.PHASE_OPEN or not self.has_enough_players:
            return False

        self.phase = self.PHASE_1
        self.save()

        for player in self.ordered_players:
            player.new_hand()

        self.game.reset_deck()

        self.current_player_index = 0
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
        self.game.set_pyramid()
        self.current_player_index = None
        self.save()
        return True

    def start_phase_3(self, save=True):
        """
        Start Phase 3 of the game.

        :return: True if Phase 3 has been started or was already running, False otherwise
        """
        if self.phase == self.PHASE_3:
            return True
        elif self.phase != self.PHASE_2:
            return False

        self.phase = self.PHASE_3
        self.save()

        player_lost = 0

        for i in range(0, len(self.ordered_players)):
            if len(self.ordered_players[player_lost].current_hand.hand.hand) < len(
                self.ordered_players[i].current_hand.hand.hand
            ):
                player_lost = i

        [player.current_hand.delete() for player in self.ordered_players]

        self.current_player_index = player_lost
        self.game.reset_deck()
        self.game.set_bus()
        if save:
            self.save()

    def phase3_guess(self, guess: str, player):
        """Handle phase 3 guess."""
        if not self.cards_left or self.phase != self.PHASE_3 or self.current_player != player:
            return None

        card = self.get_card()
        correct = self.game.bus.guess_card(guess, card)
        self.phase3_next_turn(save=False)
        self.save()
        return correct

    def phase3_next_turn(self, save=True):
        """Update phase 3 game state."""
        if self.game.bus.current_card_index >= BusGame.BUS_CARD_AMOUNT or self.game.cards_left <= 0:
            self.phase = BusGameModel.PHASE_FINISHED

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
    def has_enough_players(self) -> bool:
        """
        Check if the game has enough online players to start.

        :return: True if there are more than 1 online player in this game
        """
        return self.amount_of_players > 1

    @property
    def amount_of_players(self) -> int:
        """
        Get the amount of players in the Game.

        :return: the amount of players in this game
        """
        return self.ordered_players.count()

    @property
    def amount_of_online_players(self) -> int:
        """
        Get the amount of online players in the Game.

        :return: the amount of online players in the game
        """
        return self.ordered_players.filter(online=True).count()

    def get_amount_of_players(self) -> int:
        """
        Get the amount of players for this game.

        :return: the amount of players in this game
        """
        return self.amount_of_players

    def get_amount_of_online_players(self) -> int:
        """
        Get the amount of online players in the Game.

        :return: the amount of online players in the game
        """
        return self.amount_of_online_players

    @property
    def current_player(self):
        """
        Get the current Player in this Game.

        :return: None if there is no current player, the Player object of the current player otherwise
        """
        if self.current_player_index is not None and 0 <= self.current_player_index < self.amount_of_players:
            return self.ordered_players[self.current_player_index]

        raise ValueError("Current player index is not within player list bounds.")

    @staticmethod
    def get_card_question(player):
        """
        Get a card question.

        :param player: the Player to get a card question for
        :return: a dictionary with a 'question' attribute indicating the question and a 'answers' attribute indicating
        all possible answers in a list, returns False if the player is not a player of this game or if the player
        has more than four cards.
        """
        return BusGame.get_question_round_question(len(player.current_hand.hand.hand))

    def phase1_next_turn(self):
        """
        Rotate the turn variable in this class to indicate a next Player.

        Also starts phase 2 if necessary
        :return: None
        """
        least_cards = BusHand.MAX_CARDS_IN_HAND
        player_turn = self.current_player_index
        for i in range(0, len(self.ordered_players)):
            if len(self.ordered_players[i].current_hand.hand.hand) < least_cards:
                least_cards = len(self.ordered_players[i].current_hand.hand.hand)
                player_turn = i
        if least_cards == BusHand.MAX_CARDS_IN_HAND:
            self.start_phase_2()
        else:
            self.current_player_index = player_turn
            self.save()

    def handle_phase1_first_question(self, player, value):
        """Handle first question of phase 1."""
        card = self.get_card()
        player.current_hand.add_card_to_hand(card)
        answer = BusGame.get_question_round_question_1_outcome(value, card)
        return answer, False

    def handle_phase1_second_question(self, player, value):
        """Handle second question of phase 1."""
        drawn_card = self.get_card()
        current_card = player.current_hand.card_list[0]
        player.current_hand.add_card_to_hand(drawn_card)
        outcome = BusGame.get_question_round_question_2_outcome(value, current_card, drawn_card)
        if outcome and value == BusGame.VALUE_SAME:
            return outcome, True
        else:
            return outcome, False

    def handle_phase1_third_question(self, player, value):
        """Handle third question of phase 1."""
        drawn_card = self.get_card()
        first_card = player.current_hand.card_list[0]
        second_card = player.current_hand.card_list[1]
        player.current_hand.add_card_to_hand(drawn_card)
        outcome = BusGame.get_question_round_question_3_outcome(value, first_card, second_card, drawn_card)
        if value == BusGame.VALUE_SAME:
            return outcome, True
        else:
            return outcome, False

    def handle_phase1_fourth_question(self, player, value):
        """Handle fourth question of phase 1."""
        drawn_card = self.get_card()
        cards = [x for x in player.current_hand.hand.hand[:3]]
        player.current_hand.add_card_to_hand(drawn_card)
        outcome = BusGame.get_question_round_question_4_outcome(value, cards, drawn_card)
        if value == BusGame.VALUE_SAME:
            return outcome, True
        else:
            return outcome, False

    def handle_phase1_answer(self, player, value: int):
        """Handle a phase 1 answer."""
        if player not in self.ordered_players or player.id is not self.current_player.id:
            return None

        if len(player.current_hand.hand.hand) == 0:
            correct, group_drink = self.handle_phase1_first_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        elif len(player.current_hand.hand.hand) == 1:
            correct, group_drink = self.handle_phase1_second_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        elif len(player.current_hand.hand.hand) == 2:
            correct, group_drink = self.handle_phase1_third_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        elif len(player.current_hand.hand.hand) == 3:
            correct, group_drink = self.handle_phase1_fourth_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        else:
            return None

    @property
    def current_bus_card(self) -> BusCard:
        """Get the current bus card."""
        return self.game.bus.current_card()

    @property
    def current_pyramid_card(self) -> BusCard:
        """Get the current pyramid card."""
        return self.game.pyramid.current_card()

    def phase2_next_turn(self, index) -> bool:
        """
        Alter the game state so that the next pyramid card is displayed.

        :param index: the index of the pyramid currently
        :return: True if the game state was altered successfully, False otherwise
        """
        if index == self.game.pyramid.current_card_index:
            if not self.game.pyramid.set_next_pyramid_card():
                self.start_phase_3(save=False)
            self.save()
            return True
        else:
            return False

    def _add_card_on_pyramid(self, card: BusCard, player):
        """Add a card to the pyramid list."""
        card.owner = player
        self.game.pyramid.add_card_to_pyramid(card)
        self.save()

    def add_card_to_pile(self, player, suit, rank):
        """Add a card to the pyramid card pile while first checking if it can be removed from the player."""
        if player not in self.ordered_players:
            return False

        if player.current_hand.remove_card_from_hand(BusCard(suit, rank)):
            self._add_card_on_pyramid(BusCard(suit, rank), player)
            return True
        else:
            return False

    def id_in_pyramid(self, random_id: str):
        """Check if an id of a card is in the pyramid list."""
        return self.game.pyramid.id_in_cards_list(random_id)

    def call_card(self, random_id: str):
        """Call a card with a specific id."""
        card = self.game.pyramid.remove_card_in_pyramid_list(random_id)
        if card is not None:
            if card.owner is not None:
                card.owner.current_hand.add_card_to_hand(card)
                self.save()
                return True, card.owner
            else:
                return True, None
        else:
            return False, self.game.pyramid.owner_of_id(random_id)


class Hand(models.Model):
    """Hand model."""

    state = models.TextField(null=True, default=None)

    def __init__(self, *args, **kwargs):
        """
        Initialize BusGameModel object.

        This initializes the _hand property that holds the BusHand object. _original_state will also be initialized as
        a way to see whether the hand state was manually changed in the save method.
        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(Hand, self).__init__(*args, **kwargs)
        if self.state is None:
            self._hand = BusHand()
        else:
            self._hand = BusHand.from_json(self.state)

        self._original_state = self.state

    def save(self, *args, **kwargs):
        """
        Save method for Hand object.

        Creates a slug for the game
        :param args: arguments
        :param kwargs: keyword arguments
        :return: None
        """
        if self._original_state == self.state:
            self.state = self._hand.to_json()
            self._original_state = self.state
        super(Hand, self).save(*args, **kwargs)

    @property
    def hand(self):
        """Get the _hand object."""
        return self._hand

    def add_card_to_hand(self, card: BusCard) -> bool:
        """
        Add a card to this hand.

        :param card: the card to add
        :return: None
        """
        if self.hand.add_card(card):
            self.save()
            return True
        return False

    @property
    def card_list_add_empty(self) -> [BusCard]:
        """Get the current hand as a List while appending empty cards if list length is smaller than 4."""
        open_cards = self.hand.hand
        while len(open_cards) < BusHand.MAX_CARDS_IN_HAND:
            open_cards.append(None)
        return open_cards

    @property
    def card_list(self) -> [BusCard]:
        """Get the current hand as List."""
        return self.hand.hand

    def remove_card_from_hand(self, card: BusCard) -> bool:
        """
        Remove a card from this hand.

        :param card: the card to remove
        :return: True if the card could be removed, False otherwise
        """
        if self.hand.remove_card(card):
            self.save()
            return True
        return False


class Player(models.Model):
    """Player model."""

    PLAYER_COOKIE_NAME = "player_id"

    cookie = models.CharField(max_length=32)
    name = models.CharField(max_length=32, blank=False, null=False)
    current_game = models.ForeignKey(BusGameModel, on_delete=models.SET_NULL, null=True, default=None)
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
                if self.current_game.amount_of_players >= BusGame.MAXIMUM_AMOUNT_OF_PLAYERS:
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
