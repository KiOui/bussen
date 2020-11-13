from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import redirect

from .services import BusGame, BusHand, BusCard, BusGameConsumer
from rooms.models import Player, Room, NoRoomForGameException


class GameStateException(Exception):
    """Game state exception."""

    pass


class BusGameModel(models.Model):
    """Game model."""

    PHASE_1 = 0
    PHASE_2 = 1
    PHASE_3 = 2
    PHASE_FINISHED = 3

    PHASES = (
        (PHASE_1, "Phase 1"),
        (PHASE_2, "Phase 2"),
        (PHASE_3, "Phase 3"),
        (PHASE_FINISHED, "Finished"),
    )

    created = models.DateTimeField(auto_now_add=True)
    state = models.TextField(null=True, default=None)
    phase = models.IntegerField(choices=PHASES, default=0, null=False, blank=False)
    current_player_index = models.IntegerField(null=True, blank=False, default=0)

    @property
    def room(self) -> Room:
        ct = ContentType.objects.get_for_model(self)
        room = Room.objects.get(content_type=ct, object_id=self.id)
        if room is None:
            raise NoRoomForGameException
        else:
            return room

    def remove_player(self, player):
        try:
            Hand.objects.get(player=player, game=self).delete()
        except Hand.DoesNotExist:
            pass

        if player not in list(self.room.players)[self.current_player_index:]:
            self.current_player_index -= 1
            self.save()

        if len(list(self.room.players)) < self.minimum_amount_of_players():
            self.delete()
            return None
        return self

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
        ct = ContentType.objects.get_for_model(self)
        try:
            room = Room.objects.get(content_type=ct, object_id=self.id)
            return "Bussen ({})".format(room.name)
        except Room.DoesNotExist:
            return "Bussen (No corresponding room)"

    def save(self, *args, **kwargs):
        """
        Save method for Game object.

        :param args: arguments
        :param kwargs: keyword arguments
        :return: None
        """
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

        for i in range(0, len(self.room.players)):
            hand_player_lost = Hand.get_hand(self.room.players[player_lost], self)
            hand_player = Hand.get_hand(self.room.players[i], self)
            if len(hand_player_lost.hand.hand) < len(
                hand_player.hand.hand
            ):
                player_lost = i

        [Hand.get_hand(player, self).delete() for player in self.room.players]

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
        return self.room.players.count()

    @property
    def amount_of_online_players(self) -> int:
        """
        Get the amount of online players in the Game.

        :return: the amount of online players in the game
        """
        return self.room.players.filter(online=True).count()

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
            return self.room.players[self.current_player_index]

        raise ValueError("Current player index is not within player list bounds.")

    def get_card_question(self, player):
        """
        Get a card question.

        :param player: the Player to get a card question for
        :return: a dictionary with a 'question' attribute indicating the question and a 'answers' attribute indicating
        all possible answers in a list, returns False if the player is not a player of this game or if the player
        has more than four cards.
        """
        hand = Hand.get_hand(player, self)
        return BusGame.get_question_round_question(len(hand.hand.hand))

    def phase1_next_turn(self):
        """
        Rotate the turn variable in this class to indicate a next Player.

        Also starts phase 2 if necessary
        :return: None
        """
        least_cards = BusHand.MAX_CARDS_IN_HAND
        player_turn = self.current_player_index
        for i in range(0, len(self.room.players)):
            if len(Hand.get_hand(self.room.players[i], self).hand.hand) < least_cards:
                least_cards = len(Hand.get_hand(self.room.players[i], self).hand.hand)
                player_turn = i
        if least_cards == BusHand.MAX_CARDS_IN_HAND:
            self.start_phase_2()
        else:
            self.current_player_index = player_turn
            self.save()

    def handle_phase1_first_question(self, player, value):
        """Handle first question of phase 1."""
        card = self.get_card()
        hand = Hand.get_hand(player, self)
        hand.add_card_to_hand(card)
        answer = BusGame.get_question_round_question_1_outcome(value, card)
        return answer, False

    def handle_phase1_second_question(self, player, value):
        """Handle second question of phase 1."""
        drawn_card = self.get_card()
        hand = Hand.get_hand(player, self)
        current_card = hand.card_list[0]
        hand.add_card_to_hand(drawn_card)
        outcome = BusGame.get_question_round_question_2_outcome(value, current_card, drawn_card)
        if outcome and value == BusGame.VALUE_SAME:
            return outcome, True
        else:
            return outcome, False

    def handle_phase1_third_question(self, player, value):
        """Handle third question of phase 1."""
        drawn_card = self.get_card()
        hand = Hand.get_hand(player, self)
        first_card = hand.card_list[0]
        second_card = hand.card_list[1]
        hand.add_card_to_hand(drawn_card)
        outcome = BusGame.get_question_round_question_3_outcome(value, first_card, second_card, drawn_card)
        if value == BusGame.VALUE_SAME:
            return outcome, True
        else:
            return outcome, False

    def handle_phase1_fourth_question(self, player, value):
        """Handle fourth question of phase 1."""
        drawn_card = self.get_card()
        hand = Hand.get_hand(player, self)
        cards = [x for x in hand.hand.hand[:3]]
        hand.add_card_to_hand(drawn_card)
        outcome = BusGame.get_question_round_question_4_outcome(value, cards, drawn_card)
        if value == BusGame.VALUE_SAME:
            return outcome, True
        else:
            return outcome, False

    def handle_phase1_answer(self, player, value: int):
        """Handle a phase 1 answer."""
        if player not in self.room.players or player.id is not self.current_player.id:
            return None
        hand = Hand.get_hand(player, self)
        if len(hand.hand.hand) == 0:
            correct, group_drink = self.handle_phase1_first_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        elif len(hand.hand.hand) == 1:
            correct, group_drink = self.handle_phase1_second_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        elif len(hand.hand.hand) == 2:
            correct, group_drink = self.handle_phase1_third_question(player, value)
            self.phase1_next_turn()
            return {"drink": not correct, "group_drink": group_drink and correct}
        elif len(hand.hand.hand) == 3:
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
        self.pyramid = self.game.pyramid.add_card_to_pyramid(card)
        self.save()

    def add_card_to_pile(self, player, suit, rank):
        """Add a card to the pyramid card pile while first checking if it can be removed from the player."""
        if player not in self.room.players:
            return False
        hand = Hand.get_hand(player, self)
        if self.game.pyramid.can_add_cards() and hand.remove_card_from_hand(BusCard(suit, rank)):
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
                hand = Hand.get_hand(card.owner, self)
                hand.add_card_to_hand(card)
                self.save()
                return True, card.owner
            else:
                return True, None
        else:
            return False, self.game.pyramid.owner_of_id(random_id)

    def execute_message(self, message, player):
        if 'phase' in message.keys():
            if message['phase'] == 'phase1':
                BusGameConsumer.handle_phase1_message(message, player)
            elif message['phase'] == 'phase2':
                BusGameConsumer.handle_phase2_message(message, player)
            elif message['phase'] == 'phase3':
                BusGameConsumer.handle_phase3_message(message, player)

    @staticmethod
    def game_name():
        return "Bussen"

    @staticmethod
    def get_route():
        return "bussen:redirect"

    @staticmethod
    def get_redirect_route():
        return redirect(BusGameModel.get_route())

    @staticmethod
    def minimum_amount_of_players():
        return 2

    @staticmethod
    def maximum_amount_of_players():
        return 8


class Hand(models.Model):
    """Hand model."""

    player = models.OneToOneField(Player, on_delete=models.CASCADE, null=False, blank=False)
    game = models.ForeignKey(BusGameModel, on_delete=models.CASCADE, null=False, blank=False)
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

    def reset_hand(self, save=True):
        """Reset state."""
        self.hand.reset()
        if save:
            self.save()

    @staticmethod
    def get_hand(player: Player, game: BusGameModel):
        """Get the hand of a player."""
        hand, _ = Hand.objects.get_or_create(player=player, game=game)
        return hand
