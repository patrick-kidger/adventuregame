import Tools as tools

import config.internal_strings as internal_strings

### Settings ###

WINDOW_NAME = 'Maze Game'

# How many ticks of physics should be done each second.
PHYSICS_FRAMERATE = 120
# How long a key should be held down for to generate repeat keypresses. Must be somewhat larger than TICK_PAUSE, so that
# events don't build up faster than the game can process them.
KEY_REPEAT = 50

# How many physics ticks it should take to fall through one z-level
FALL_TICKS = 15

# The file extension for map files
MAP_FILE_EXTENSION = 'map'

# The name of the folder containing the map data
MAP_FOLDER = 'map_data'

# The names of the folders containing the interface / tile / entity images respectively
INTERFACE_FOLDER = 'interface'
TILE_FOLDER = 'tiles'
ENTITY_FOLDER = 'entities'

# The sizes of the tiles, in pixels
TILE_Y = 32
TILE_X = 32


### Output ###
# These determine how the game is rendered onto the screen.
# Note that this is distinct from the strings module: here we handle the actual game.
# Strings handles the talking-to-the-user interface.

SCREEN_SIZE = (1600, 900)  # The overall size of the screen

# Graphics overlay options
GRAPHICS_SCREEN_SIZE = (1600, 900)  # The size of the debug overlay
GRAPHICS_SCREEN_LOC = (0, 0)  # The location of the graphics overlay on hte main screen
GRAPHICS_BACKGROUND_COLOR = (255, 255, 255)  # White

# Debug overlay options
DEBUG_FONT_NAME = "Monospace"
DEBUG_FONT_SIZE = 20
DEBUG_FONT_COLOR = (0, 0, 0)  # Black

DEBUG_SCREEN_SIZE = (1600, 600)  # The size of the debug overlay
DEBUG_SCREEN_LOC = (0, 300)  # The location of the debug overlay on the main screen
DEBUG_BACKGROUND_COLOR = (200, 200, 200)  # Grey

# Menu overlay text options
MENU_FONT_NAME = "Monospace"
MENU_FONT_SIZE = 20
MENU_FONT_COLOR = (0, 0, 0)  # Black

MENU_BACKGROUND_COLOR = (255, 255, 255)  # White

### Input ###
# These define the input that the game is expecting, and should line up with e.g.
# the standard keyboard keycodes. We also define messages regarding the input here.

# Moving around. All commands here should in lower case.
class Move(tools.Container):
    """All valid inputs for moving around."""
    DOWN = 's'
    UP = 'w'
    LEFT = 'a'
    RIGHT = 'd'
    VERTICAL_UP = 'r'
    VERTICAL_DOWN = 'f'
    Direction = {DOWN: internal_strings.Play.DOWN, UP: internal_strings.Play.UP, LEFT: internal_strings.Play.LEFT,
                 RIGHT: internal_strings.Play.RIGHT, VERTICAL_UP: internal_strings.Play.VERTICAL_UP,
                 VERTICAL_DOWN: internal_strings.Play.VERTICAL_DOWN}
    
class DebugCommands(tools.Container):
    """All valid commands in the console"""
    DEBUG = 'debug'
    CLEAR = 'clear'
    HELP = 'help'
    NOCLIP = 'noclip'
    FLY = 'fly'
    GHOST = 'ghost'
    GET = 'get'
    QUIT = 'quit'
    EXIT = 'exit'   # Does the same thing as quit
    CLOSE = 'close'  # Does not do the same thing as quit
    RESET = 'reset'

# Button to toggle the console
OPEN_CONSOLE = '\\'
# Button to select the console
SELECT_CONSOLE = '/'
# How many of its past commands the console should remember
CONSOLE_MEMORY_SIZE = 10
# What the prompt should be in the console
CONSOLE_PROMPT = '> '
