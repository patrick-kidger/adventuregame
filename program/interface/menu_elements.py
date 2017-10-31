import Tools as tools


import config.config as config

import program.interface.base as base
import program.misc.helpers as helpers
import program.misc.sdl as sdl


class MenuElement(helpers.image_from_filename(config.INTERFACE_FOLDER)):
    def __init__(self, screen, *args, **kwargs):
        self.screen = screen
        self.uuid = tools.uuid()
        super(MenuElement, self).__init__(*args, **kwargs)

    def __hash__(self):
        return self.uuid


class Button(MenuElement, base.FontMixin):
    size_image = 'button_base'

    class ImageFilenames(tools.Container):
        button_base = 'general/button/button_base.png'
        button_deselect = 'general/button/button_deselect.png'
        button_select = 'general/button/button_select.png'


class List(MenuElement, base.FontMixin):
    size_image = 'list_background'

    class ImageFilenames(tools.Container):
        list_background = 'general/list/list_background.png'
        list_base = 'general/list/list_base.png'
        list_entry_base = 'general/list/list_entry_base.png'
        list_entry_deselected = 'general/list/list_entry_deselected.png'
        list_entry_selected = 'general/list/list_entry_selected.png'
        list_scroll_handle = 'general/list/list_scroll_handle.png'

    class Alignment(object):
        scroll_screen_dim = (747, 735)
        scroll_screen_offset = (5, 60)
        entry_offset = (18, 18)
        title_offset = (8, 8)

    def __init__(self, screen, title, entries, font, *args, **kwargs):
        super(List, self).__init__(screen, font, *args, **kwargs)
        self.scrolled_amount = 0
        entry_rect = self.Images.list_entry_base.get_rect()
        self.scroll_screen = sdl.Surface((entry_rect.width, entry_rect.height * len(entries)))
        scroll_screen_rect = sdl.Rect(self.Alignment.scroll_screen_offset, self.Alignment.scroll_screen_dim)
        self.scroll_screen_view = self.screen.subsurface(scroll_screen_rect)

        self.scroll_screen.fill(config.MENU_BACKGROUND_COLOR)
        for i, entry in enumerate(entries):
            self.scroll_screen.blit(self.Images.list_entry_base, (0, entry_rect.height * i))
            self.scroll_screen.blit(self.Images.list_entry_deselected, (0, entry_rect.height * i))
            entry_text = self.render_text(entry)
            entry_offset = self.Alignment.entry_offset
            self.scroll_screen.blit(entry_text, (0 + entry_offset[0], (entry_rect.height * i) + entry_offset[1]))

        self.screen.blit(self.Images.list_base, (0, 0))
        self.screen.blit(self.Images.list_background, (0, 0))
        title_text = self.render_text(title)
        self.screen.blit(title_text, self.Alignment.title_offset)
        self.scroll_screen_view.blit(self.scroll_screen, (0, self.scrolled_amount))
