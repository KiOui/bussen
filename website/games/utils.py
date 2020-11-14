class Games:
    """Class to keep track of all added games."""

    def __init__(self):
        """Initialize class."""
        self.games = dict()

    def add_game(self, name, cls):
        """Add a game to the games list."""
        self.games[name] = cls

    def get_games(self):
        """Get all games in the games list."""
        return self.games


"""
To add a new game, import games from games.utils and add it with games.add_game(game_name, game_main_class).
"""
games = Games()
