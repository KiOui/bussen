from django import forms
from .models import Room


class RoomCreationForm(forms.Form):
    """Room Creation form."""

    room_name = forms.CharField(max_length=128, required=True)

    def clean_room_name(self):
        """Clean room name."""
        if Room.objects.filter(name=self.cleaned_data.get("room_name")).exists():
            self.add_error("room_name", "This room already exists")
            raise forms.ValidationError("This room already exists")

        return self.cleaned_data.get("room_name")


class PlayerCreationForm(forms.Form):
    """Player Creation form."""

    player_name = forms.CharField(max_length=128, required=True)
