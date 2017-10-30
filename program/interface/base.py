class BaseIO(object):
    def __init__(self):
        self.inp = None
        self.out = None
        super(BaseIO, self).__init__()

    def register_interface(self, interface):
        """Lets the BaseIO instance know what interface it is used with."""
        self.inp = interface.inp
        self.out = interface.out
