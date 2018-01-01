import collections
import Tools as tools


import Game.config.strings as strings
import Game.config.internal as internal

import Game.program.interface.menu_elements as menu_elements
import Game.program.interface.base as base
import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


class MenuOverlay(base.FontMixin, base.AlignmentMixin, base.GraphicsOverlay):
    """A graphics overlay for menus. This overlay is rather special, in that it does not define a __call__ method.
    Instead it provides methods for placing menu elements on the screen. Subsequently making a call to an associated
    menu listener will then determine which of these menu elements are interacted with."""

    def reset(self):
        super(MenuOverlay, self).reset()
        self.screen.clear_cutouts()
        # All menu elements
        self.menu_elements = collections.deque()
        # Those elements which must have non-None data set before the menu can be 'submitted', i.e. pass data back to
        # the game.
        self.necessary_elements = set()
        # Those elements which, when interacted with, will attempt to 'submit' the current menu.
        self.submit_elements = set()
        # As submit_elements, but do not require the necessary elements to have non-None data to submit. (i.e. for
        # returning to earlier menus)
        self.back_elements = set()

        # The last element that we clicked
        self._selected_element = None
        # Whether we are currently still clicking the element. (i.e. we are in between mousedown and mouseup)
        self._mouse_is_down = False
        # The current state of all the menu elements
        self._menu_results = tools.deldefaultdict(lambda: None)

    def remove(self, element):
        self.screen.discard_cutout(element.screen)
        self.menu_elements.remove(element)
        self.necessary_elements.discard(element)
        self.submit_elements.discard(element)
        self.back_elements.discard(element)

        if element is self._selected_element:
            self._selected_element = None
        del self._menu_results[element]

    def handle(self, event):
        returnval = None
        if sdl.event.is_mouse(event, valid_buttons=(1, 4, 5)):
            menu_element = self._find_element(event.pos)

            if event.type == sdl.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self._left_click(event, menu_element)
                elif event.button in (4, 5):  # Scroll wheel
                    self._scroll(event, menu_element)
                else:
                    raise exceptions.ProgrammingException

            elif event.type == sdl.MOUSEBUTTONUP:
                returnval = self._mouseup(event, menu_element)

            elif event.type == sdl.MOUSEMOTION:
                self._mousemotion(event, menu_element)
                self._mouseover(event, menu_element)

            else:
                raise exceptions.ProgrammingException

            if returnval is not None:
                return returnval, internal.InputTypes.MENU
        else:
            raise exceptions.UnhandledInput

    def _left_click(self, event, menu_element):
        """Handles left clicking on a menu element. Pulled out as a separate function for clarity."""

        self._mouse_is_down = True

        # Unclick the previous menu element
        self._un_mousedown(menu_element)

        # Click this menu element
        self._selected_element = menu_element
        if menu_element is not None:
            element_pos = menu_element.screen_pos(event.pos)
            click_result, store_result = menu_element.mousedown(self._menu_results, element_pos)
            if store_result:
                self._menu_results[menu_element] = click_result
        else:
            raise exceptions.UnhandledInput

    def _un_mousedown(self, menu_element):
        if self._selected_element is not None and self._selected_element is not menu_element:
            self._selected_element.un_mousedown(self._menu_results)

    def _scroll(self, event, menu_element):
        if menu_element is not None:
            element_pos = menu_element.screen_pos(event.pos)
            is_scroll_up = (event.button == 4)
            click_result, store_result = menu_element.scroll(self._menu_results, is_scroll_up, element_pos)
            if store_result:
                self._menu_results[menu_element] = click_result
        else:
            raise exceptions.UnhandledInput

    def _mouseup(self, event, menu_element):
        self._mouse_is_down = False
        if self._selected_element is not None:
            element_pos = self._selected_element.screen_pos(event.pos)
            click_result, store_result = self._selected_element.mouseup(self._menu_results, element_pos)
            if store_result:
                self._menu_results[self._selected_element] = click_result

            # We potentially return data if we click a submit or back element
            if self._selected_element in self.submit_elements:
                # Make sure all necessary elements have data
                for necessary_element in self.necessary_elements:
                    if self._menu_results[necessary_element] is None:
                        break  # Necessary element doesn't have data
                else:
                    # All necessary elements have data; we're done here.
                    return click_result
            elif self._selected_element in self.back_elements:
                return click_result
        else:
            raise exceptions.UnhandledInput

    def _mousemotion(self, event, menu_element):
        if self._mouse_is_down and self._selected_element is not None:
            element_pos = self._selected_element.screen_pos(event.pos)
            click_result, store_result = self._selected_element.mousemotion(self._menu_results, element_pos)
            if store_result:
                self._menu_results[self._selected_element] = click_result
        else:
            raise exceptions.UnhandledInput

    def _mouseover(self, event, menu_element):
        if menu_element is not None:
            element_pos = menu_element.screen_pos(event.pos)
            click_result, store_result = menu_element.mouseover(self._menu_results, element_pos)
            if store_result:
                self._menu_results[menu_element] = click_result
        else:
            raise exceptions.UnhandledInput

    def _find_element(self, pos):
        """Returns the menu element that the given position is over, or None if it is not over any menu element."""
        for menu_element in self.menu_elements:
            if menu_element.screen.point_within_offset(pos):
                return menu_element

    def list(self, title, entry_text, necessary=False, **kwargs):
        """Creates a list with the given title, entries, and alignment.

        :str title: The title to put at the top of the list.
        :iter[str] entries: The entries to put in the list.
        :bool necessary: Optional argument determining whether or not this element must have non-None data set before
            the menu can be submitted. If not passed, defaults to False..
        :str horz_alignment: Optional argument. An internal.Alignment attribute defining the horizontal
            placement of the list on the overlay's screen. If not passed, defaults to the center of the screen.
        :str vert_alignment: Optional argument. As horz_alignment, for vertical placement. If not passed, defaults to
            the center of the screen.
        """
        # Not specified as arguments above so that they automatically use the default argument values in self._view
        align_kwargs = tools.extract_keys(kwargs, ['horz_alignment', 'vert_alignment'])

        list_screen = sdl.Surface.from_rect(menu_elements.List.size)
        list_screen.fill(self.background_color)
        self._view_cutout(list_screen, **align_kwargs)
        created_list = menu_elements.List(screen=list_screen, title=title, entry_text=entry_text, font=self.font)
        self.menu_elements.appendleft(created_list)
        if necessary:
            self.necessary_elements.add(created_list)
        return created_list

    def messagebox(self, title, text, buttons=(strings.Menus.OK,), select=False, **kwargs):
        # Not specified as arguments above so that they automatically use the default argument values in self._view
        align_kwargs = tools.extract_keys(kwargs, ['horz_alignment', 'vert_alignment'])
        messagebox_screen = sdl.Surface.from_rect(menu_elements.MessageBox.size)
        messagebox_screen.fill(self.background_color)
        self._view_cutout(messagebox_screen, **align_kwargs)
        created_messagebox = menu_elements.MessageBox(screen=messagebox_screen, title=title, text=text, buttons=buttons,
                                                      font=self.font)
        self.menu_elements.appendleft(created_messagebox)
        if select:
            self._un_mousedown(None)
            self._selected_element = created_messagebox
        return created_messagebox

    def button(self, text, necessary=False, **kwargs):
        """Creates a button with the given text.

        :str text: The text to put on the button.
        :press: The value that is returned when this button is pressed
        :bool necessary: As in the method 'list'.
        :str horz_alignment: As in the method 'list'.
        :str vert_alignment: As in the method 'list'.
        """
        # Not specified as arguments above so that they automatically use the default argument values in self._view
        align_kwargs = tools.extract_keys(kwargs, ['horz_alignment', 'vert_alignment'])

        button_screen = sdl.Surface.from_rect(menu_elements.Button.size)
        button_screen.fill(self.background_color)
        self._view_cutout(button_screen, **align_kwargs)
        created_button = menu_elements.Button(screen=button_screen, text=text, font=self.font)
        self.menu_elements.appendleft(created_button)
        if necessary:
            self.necessary_elements.add(created_button)
        return created_button

    def submit(self, text, horz_alignment=internal.Alignment.RIGHT,
               vert_alignment=internal.Alignment.BOTTOM):
        """Creates a submit button with the given text - pressing this button will attempt to submit the menu.

        :str text: The text to put on the submit button.
        :str horz_alignment: As in the method 'list', but defaults to the right.
        :str vert_alignment: As in the method 'list', but defaults to the bottom."""
        submit_button = self.button(text, horz_alignment=horz_alignment, vert_alignment=vert_alignment)
        self.submit_elements.add(submit_button)
        return submit_button

    def back(self, text, horz_alignment=internal.Alignment.LEFT,
             vert_alignment=internal.Alignment.BOTTOM):
        """Creates a back button with the given text - pressing this button is a submit button, as above, but that
        does not require necessary elements to have data."""
        back_button = self.button(text, horz_alignment=horz_alignment, vert_alignment=vert_alignment)
        self.back_elements.add(back_button)
        return back_button
