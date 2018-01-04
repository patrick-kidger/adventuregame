import os


import Game.config.internal as internal

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


class BaseOverlay:
    def __init__(self, name, location, size, background_color, *args, **kwargs):
        super(BaseOverlay, self).__init__(*args, **kwargs)
        # Name of the overlay!
        self.name = name
        # Where it is visually on the screen.
        self.location = sdl.Rect(location, size)
        # What is is visually, on the screen.
        self.screen = sdl.Surface(size)
        self.screen.set_offset(location)
        # The background colour of its screen
        self.background_color = background_color
        # The keys (on the keyboard) that should give KEYDOWN events whilst being *held* down.
        self.listen_keys = set()
        # The mouse buttons that should give MOUSEBUTTONDOWN events whilst being *held* down.
        self.listen_mouse = set()
        # Whether the screen is visible
        self.screen_enabled = False
        # Whether the interface should listen for inputs
        self.listen_enabled = False
        # The game itself
        self._game_instance = None
        # An interface (technical term) to the overall interface (non-technical term) (!)
        self._interface_overlayer = None
        # Whether an overlay should be closed if it loses the selection
        self.must_be_top = False

        self.reset()

    def reset(self):
        self.wipe()
        # Endpoint for super calls.

    def register_interface(self, interface_overlayer):
        self._interface_overlayer = interface_overlayer

    def handle(self, event):
        raise NotImplementedError

    def output(self, *args, **kwargs):
        raise NotImplementedError

    def wipe(self):
        """Fills the screen with its background color."""
        self.screen.fill(self.background_color)

    def enable(self, state=True):
        """Sets the enabled attributes to 'state', or True if no 'state' argument is passed."""
        self.screen_enabled = state
        self.listen_enabled = state

    def disable(self):
        """Sets the enabled attributes to False."""
        self.enable(False)

    def toggle(self):
        """Toggles whether the overlay is enabled."""
        self.listen_enabled = not self.screen_enabled  # Deliberately screen_enabled, not listen_enabled
        self.screen_enabled = not self.screen_enabled

    def enable_listener(self, state=True):
        """Sets the listener_enabled attribute to 'state', or True if no 'state' argument is passed."""
        self.listen_enabled = state

    def disable_listener(self):
        """Sets the listener_enabled attribute to False."""
        self.enable_listener(False)

    def toggle_listener(self):
        """Toggles whether just the listener of the overlay is enabled."""
        self.listen_enabled = not self.listen_enabled


class GraphicsOverlay(BaseOverlay):
    def output(self, source, dest=(0, 0), area=None, special_flags=0, offset=None, *args, **kwargs):
        if offset is not None:
            dest = dest[0] - offset.x, dest[1] - offset.y
        self.screen.blit_offset(source, dest, area, special_flags)


class AlignmentMixin:
    """Provides methods for placing objects on the instances's screen. The instance must already have a screen for this
    to work - this mixin does not provide one."""

    def _align(self, image_rect, horz_alignment=internal.Alignment.CENTER, vert_alignment=internal.Alignment.CENTER):
        """Takes a rectangle and some alignment options and returns the coordinates that the top left of the rectangle
        should be at on the instance's screen.

        :Rect image_rect: pygame.Rect instance of the object to tbe placed.
        :str horz_alignment: Optional string describing where the object should be placed.
        :str vert_alignment: Optional string describing where the object should be placed.
        """

        screen_rect = self.screen.get_rect()
        if horz_alignment == internal.Alignment.LEFT:
            horz_pos = 0
        elif horz_alignment == internal.Alignment.RIGHT:
            horz_pos = screen_rect.width - image_rect.width
        elif horz_alignment == internal.Alignment.CENTER:
            horz_pos = (screen_rect.width - image_rect.width) // 2
        else:
            horz_pos = horz_alignment

        if vert_alignment == internal.Alignment.TOP:
            vert_pos = 0
        elif vert_alignment == internal.Alignment.BOTTOM:
            vert_pos = screen_rect.height - image_rect.height
        elif vert_alignment == internal.Alignment.CENTER:
            vert_pos = (screen_rect.height - image_rect.height) // 2
        else:
            vert_pos = vert_alignment

        return horz_pos, vert_pos

    def _view_rect(self, image_rect, horz_alignment=internal.Alignment.CENTER, vert_alignment=internal.Alignment.CENTER):
        """Takes a rectangle and some alignment options and returns the rectangle, translated according to the alignment
        options."""
        horz_pos, vert_pos = self._align(image_rect, horz_alignment, vert_alignment)
        moved_image_rect = sdl.Rect(horz_pos, vert_pos, image_rect.width, image_rect.height)
        return moved_image_rect

    def _view(self, image_rect, horz_alignment=internal.Alignment.CENTER, vert_alignment=internal.Alignment.CENTER):
        """As _align, but returns a subsurface of the instance's screen corresponding to where :image_rect: should be
        placed."""
        moved_image_rect = self._view_rect(image_rect, horz_alignment, vert_alignment)
        return self.screen.subsurface(moved_image_rect)

    def _view_cutout(self, target, horz_alignment=internal.Alignment.CENTER, vert_alignment=internal.Alignment.CENTER):
        """As _view, but instead wires up an already created screen using cutouts."""
        cutout_rect = self._view_rect(target.get_rect(), horz_alignment, vert_alignment)
        self.screen.cutout(cutout_rect, target)


def font(font_filepath, font_size, font_color):
    """Wrapper around pygame's fonts."""
    abs_font_filepath = os.path.join(os.path.dirname(__file__), '..', '..', 'data', font_filepath)
    font = sdl.freetype.Font(abs_font_filepath, font_size)
    font.fgcolor = font_color
    font.pad = True
    return font


class FontMixin:
    """Allows for using fonts, for text."""
    def __init__(self, font, *args, **kwargs):
        self.font = font
        super(FontMixin, self).__init__(*args, **kwargs)

    def render_text(self, text):
        surf, rect = self.font.render(text)
        return surf

    def render_text_with_newlines(self, text_pieces, background=(255, 255, 255)):
        if len(text_pieces) == 0:
            raise exceptions.ProgrammingException
        rendered_pieces = []
        font_height = self.font.get_sized_height()
        total_height = font_height * len(text_pieces)
        max_width = 0
        for piece in text_pieces:
            rendered_piece = self.render_text(piece)
            max_width = max(max_width, rendered_piece.get_rect().width)
            rendered_pieces.append(rendered_piece)
        return_surf = sdl.Surface((max_width, total_height))
        return_surf.fill(background)
        cursor = 0
        for rendered_piece in rendered_pieces:
            return_surf.blit(rendered_piece, (0, cursor))
            cursor += font_height
        return return_surf
