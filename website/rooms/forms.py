from django import forms
from .models import Player


class GameCreationForm(forms.Form):
    """Game Creation form."""

    game_name = forms.CharField(max_length=128, required=True)


class PlayerCreationForm(forms.Form):
    """Player Creation form."""

    player_name = forms.CharField(max_length=128, required=True)

    def __init__(self, game, *args, **kwargs):
        """
        Initialise the PlayerCreationForm.

        :param game: the game to create a player for
        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(PlayerCreationForm, self).__init__(*args, **kwargs)
        self.game = game

    def clean_player_name(self):
        """
        Clean the player name.

        :return: the player_name argument if there is no other player with the same name in the game already
        """
        player_name = self.cleaned_data.get("player_name")
        if Player.objects.filter(current_game=self.game, name=player_name).exists():
            raise forms.ValidationError("This player name is already being used.")
        return player_name
