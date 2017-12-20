"""Internal values an constants for the program. These are essentially just here to ensure they are consistent
throughout the program. """

import os
import Tools as tools


import Game.config.config as config


class Move(tools.Container):
    """Movement commands for the player."""

    DOWN = 'down'
    UP = 'up'
    LEFT = 'left'
    RIGHT = 'right'


class Action(tools.Container):
    """Other commands for the player."""

    VERTICAL_UP = 'vert_up'
    VERTICAL_DOWN = 'vert_down'


class MenuIdentifiers(tools.Container):
    """Names for menus."""

    MAIN_MENU = 'main_menu'
    MAP_SELECT = 'map_select'
    OPTIONS = 'options'
    GAME_START = 'game_start'  # Not a menu; special value to indicate that the main game should be started


class Maps(tools.Container):
    """Constants relating to maps."""

    MAP_LOC = os.path.join(os.path.dirname(__file__), '..', *config.MAP_FOLDER.split('/'))


class InputTypes(tools.Container):
    """Types of player input."""

    MENU = 'menu'
    ACTION = 'action'
    NO_INPUT = 'no_input'


class Alignment(tools.Container):
    """Defines alignments when placing interface elements."""

    LEFT = 'left'
    RIGHT = 'right'
    TOP = 'top'
    BOTTOM = 'bottom'
    CENTER = 'center'


class TileRotation(tools.Container):
    """How a tile may be rotated."""

    DOWN = 'down'
    UP = 'up'
    LEFT = 'left'
    RIGHT = 'right'


class StairDirection(tools.Container):
    """Used to define whether a set of stairs go up, down, neither or both."""

    VERTICAL_UP = 'vert_up'
    VERTICAL_DOWN = 'vert_down'


class Geometry(tools.Container):
    """Used to define the geometry of a wall."""

    ANGLED = 'angled'
    CONCAVE = 'concave'
    CONVEX = 'convex'
    DOUBLE_CONCAVE = 'doub_conc'
    DOUBLE_CONVEX = 'doub_conv'
    CIRCLE = 'circle'
    SQUARE = 'square'


class MapEditor(tools.Container):
    """Constants relating to the map editor."""

    START_POS = 'start_pos'
    START_POS_MARKER = os.path.join(os.path.dirname(__file__), '..', 'tools', 'images', 'start_pos.png')
    EMPTY = os.path.join(os.path.dirname(__file__), '..', 'tools', 'images', 'empty.png')


class Helpers(tools.Container):
    """Constants relating to the abstract helpers."""

    IMAGE_LOC = os.path.join(os.path.dirname(__file__), '..')
