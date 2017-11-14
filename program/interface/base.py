import program.misc.sdl as sdl


class BaseIO(object):
    """Base class for all interface objects. Gives them 'inp' and 'out' attributes allowing the object to access the
    rest of the interface."""
    def __init__(self, *args, **kwargs):
        self.inp = None
        self.out = None
        super(BaseIO, self).__init__(*args, **kwargs)

    def register_interface(self, interface):
        """Lets the BaseIO instance know what interface it is used with."""
        self.inp = interface.inp
        self.out = interface.out
        # Endpoint for super calls.


class Font(object):
    """Wrapper around pygame's fonts."""
    def __init__(self, font_name, font_size, font_color):
        self.font = sdl.ftfont.SysFont(font_name, font_size)
        self.color = font_color

    def render(self, text):
        """Takes the given text and renders it in this font, returning a pygame.Surface object of the rendered text."""
        return self.font.render(text, False, self.color)


class FontMixin(object):
    """Allows for using fonts, for text."""
    def __init__(self, font, *args, **kwargs):
        self.font = font
        super(FontMixin, self).__init__(*args, **kwargs)

    def render_text(self, text):
        return self.font.render(text)
