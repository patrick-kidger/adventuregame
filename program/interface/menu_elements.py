import Tools as tools


import config.config as config

import program.interface.base as base
import program.misc.helpers as helpers
import program.misc.sdl as sdl


class MenuElement(helpers.image_from_filename(config.INTERFACE_FOLDER)):
    def __init__(self, screen, *args, **kwargs):
        self.screen = screen
        super(MenuElement, self).__init__(*args, **kwargs)



    @staticmethod
    def pos_diff(pos_a, pos_b):
        return pos_a[0] - pos_b[0], pos_a[1] - pos_b[1]


class Button(MenuElement, base.FontMixin, helpers.AlignmentMixin):
    size_image = 'button_base'

    class ImageFilenames(tools.Container):
        button_base = 'general/button/button_base.png'
        button_deselect = 'general/button/button_deselect.png'
        button_select = 'general/button/button_select.png'

    def __init__(self, screen, text, font, *args, **kwargs):
        super(Button, self).__init__(screen=screen, font=font, *args, **kwargs)
        self.screen.blit(self.Images.button_base)
        self.screen.blit(self.Images.button_deselect)
        button_text = self.render_text(text)
        text_centered = self._align(button_text.get_rect())
        self.screen.blit(button_text, text_centered)

    def click(self, pos):
        self.screen.blit(self.Images.button_select)

    def unclick(self):
        self.screen.blit(self.Images.button_deselect)


class _Entry(MenuElement, base.FontMixin):
    size_image = 'list_entry_base'

    text_offset = (18, 18)

    class ImageFilenames(tools.Container):
        list_entry_base = 'general/list/list_entry_base.png'
        list_entry_deselected = 'general/list/list_entry_deselected.png'
        list_entry_selected = 'general/list/list_entry_selected.png'

    def __init__(self, screen, text, font, *args, **kwargs):
        super(_Entry, self).__init__(screen=screen, font=font, *args, **kwargs)
        self.screen.blit(self.Images.list_entry_base)
        self.screen.blit(self.Images.list_entry_deselected)
        entry_text = self.render_text(text)
        text_offset = self.text_offset
        self.screen.blit(entry_text, (text_offset[0], text_offset[1]))

    def click(self):
        self.screen.blit(self.Images.list_entry_selected)

    def unclick(self):
        self.screen.blit(self.Images.list_entry_deselected)


class List(MenuElement, base.FontMixin):
    size_image = 'list_background'

    class ImageFilenames(tools.Container):
        list_background = 'general/list/list_background.png'
        list_base = 'general/list/list_base.png'
        list_scroll_handle = 'general/list/list_scroll_handle.png'

    class Alignment(object):
        scroll_screen_dim = (747, 735)
        scroll_screen_offset = (5, 60)
        title_offset = (8, 8)

    def __init__(self, screen, title, entries, font, *args, **kwargs):
        super(List, self).__init__(screen=screen, font=font, *args, **kwargs)
        self.scrolled_amount = 0
        self.entries = []
        self.clicked_entry = None
        self.scroll_screen = None
        self.scroll_screen_view = None

        entry_size = _Entry.Images.list_entry_base.get_rect()
        self.scroll_screen = sdl.Surface((entry_size.width, entry_size.height * len(entries)))
        scroll_screen_rect = sdl.Rect(self.Alignment.scroll_screen_offset, self.Alignment.scroll_screen_dim)
        self.scroll_screen_view = self.screen.subsurface(scroll_screen_rect)

        self.scroll_screen.fill(config.MENU_BACKGROUND_COLOR)
        for i, text in enumerate(entries):
            entry_rect = sdl.Rect(0, entry_size.height * i, entry_size.width, entry_size.height)
            entry_screen = self.scroll_screen.subsurface(entry_rect)
            entry = _Entry(entry_screen, text, self.font)
            self.entries.append(entry)

        self.screen.blit(self.Images.list_base)
        self.screen.blit(self.Images.list_background)
        title_text = self.render_text(title)
        self.screen.blit(title_text, self.Alignment.title_offset)
        self.update_scroll_view()

    def update_scroll_view(self):
        self.scroll_screen_view.blit(self.scroll_screen, (0, self.scrolled_amount))

    def click(self, pos):
        offset = self.screen.get_offset()
        screen_pos = self.pos_diff(pos, offset)
        scroll_view_pos = self.pos_diff(screen_pos, self.Alignment.scroll_screen_offset)
        scroll_screen_pos = scroll_view_pos[0], scroll_view_pos[1] + self.scrolled_amount
        if self.clicked_entry is not None:
            self.clicked_entry.unclick()
        for i, entry in enumerate(self.entries):
            if entry.screen.point_within(scroll_screen_pos):
                clicked_index = i
                self.clicked_entry = entry
                entry.click()
                break
        else:
            clicked_index = None
            self.clicked_entry = None
        self.update_scroll_view()

        return clicked_index

    def unclick(self):
        pass
