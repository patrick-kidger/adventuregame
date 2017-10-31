import program.misc.sdl as sdl


class BaseIO(object):
    def __init__(self, *args, **kwargs):
        self.inp = None
        self.out = None
        super(BaseIO, self).__init__(*args, **kwargs)

    def register_interface(self, interface):
        """Lets the BaseIO instance know what interface it is used with."""
        self.inp = interface.inp
        self.out = interface.out


class Font(object):
    def __init__(self, font_name, font_size, font_color):
        self.font = sdl.ftfont.SysFont(font_name, font_size)
        self.color = font_color

    def render(self, text):
        return self.font.render(text, False, self.color)


class FontMixin(object):
    """Allows for using fonts, for text."""
    def __init__(self, font, *args, **kwargs):
        self.font = font
        super(FontMixin, self).__init__(*args, **kwargs)

    def render_text(self, text):
        return self.font.render(text)