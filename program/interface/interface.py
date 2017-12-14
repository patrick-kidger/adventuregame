class Interface:
    """Wrapper around Output and Input, in order to provide the overall interface."""

    def __init__(self, inp, out):
        self.out = out
        self.inp = inp
        self.out.register_interface(self)
        self.inp.register_interface(self)

    def register_game(self, game_instance):
        self.inp.register_game(game_instance)
