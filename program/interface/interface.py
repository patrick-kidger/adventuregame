class Interface(object):
    """Wrapper around Output and Input, in order to provide the overall interface."""

    def __init__(self, inp, out):
        self.inp = inp
        self.out = out
        self.inp.register_interface(self)
        self.out.register_interface(self)
