import Game.program.misc.sdl as sdl


class BaseIO:
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


class Font:
    """Wrapper around pygame's fonts."""
    def __init__(self, font_name, font_size, font_color):
        self.font = sdl.ftfont.SysFont(font_name, font_size)
        self.color = font_color

    def render(self, text):
        """Takes the given text and renders it in this font, returning a pygame.Surface object of the rendered text."""
        return self.font.render(text, False, self.color)


class FontMixin:
    """Allows for using fonts, for text."""
    def __init__(self, font, *args, **kwargs):
        self.font = font
        super(FontMixin, self).__init__(*args, **kwargs)

    def render_text(self, text):
        return self.font.render(text)

    def render_text_with_newlines(self, text_pieces, background=(255, 255, 255)):
        rendered_pieces = []
        total_height = 0
        max_width = 0
        for piece in text_pieces:
            rendered_piece = self.render_text(piece)
            piece_rect = rendered_piece.get_rect()
            max_width = max(max_width, piece_rect.width)
            total_height += piece_rect.height
            rendered_pieces.append(rendered_piece)
        return_surf = sdl.Surface((max_width, total_height))
        return_surf.fill(background)
        cursor = 0
        for rendered_piece in rendered_pieces:
            return_surf.blit(rendered_piece, (0, cursor))
            cursor += rendered_piece.get_rect().height
        return return_surf


