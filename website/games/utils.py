
class Games:

    def __init__(self):
        self.games = dict()

    def add_game(self, name, cls):
        self.games[name] = cls

    def get_games(self):
        return self.games


games = Games()
