import Tools as tools

import Maze.config.internal_strings as internal_strings

### Settings ###

WINDOW_NAME = 'Maze Game'

# Pygame output options
SCREEN_SIZE = (1600, 900)  # The overall size of the screen
DEBUG_SCREEN_SIZE = (1600, 600)  # The size of the debug overlay
DEBUG_SCREEN_LOC = (0, 300)  # The location of the debug overlay on the main screen
DEBUG_BACKGROUND_COLOR = (200, 200, 200)  # Grey
GRAPHICS_SCREEN_SIZE = (1600, 900)  # The size of the debug overlay
GRAPHICS_SCREEN_LOC = (0, 0)  # The location of the graphics overlay on hte main screen
GRAPHICS_BACKGROUND_COLOR = (255, 255, 255)  # White

# Debug overlay text options
FONT_NAME = "Monospace"
FONT_SIZE = 20
FONT_COLOR = (0, 0, 0)  # Black

# How long to wait at each state when skipping user input.
SKIP_PAUSE = 0.1  # In seconds
# How long to pause between ticks of the game
TICK_PAUSE = 0.01  # In seconds

# The file extension for map files
MAP_FILE_EXTENSION = 'map'

# The names of the folder containing the map files / tile images / entity images respectively
MAP_FOLDER = 'map_data'
TILE_FOLDER = 'tile_data'
ENTITY_FOLDER = 'entity_data'

# The sizes of the tiles, in pixels
TILE_Y = 32
TILE_X = 32


### Output ###
# These determine how the game is rendered onto the screen.
# Note that this is distinct from the strings module: here we handle the actual game.
# Strings handles the talking-to-the-user interface.

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
    
class DebugInput(tools.Container):
    """All valid inputs in the console"""
    DEBUG = 'debug'
    CLEAR = 'clear'
    HELP = 'help'
    NOCLIP = 'noclip'
    FLY = 'fly'
    GHOST = 'ghost'
    GET = 'get'
    QUIT = 'quit'
    EXIT = 'exit'  # Does the same thing as quit
    RENDER = 'render'
    RESET = 'reset'
    CHANGEMAP = 'changemap'

# Button to toggle the console
OPEN_CONSOLE = '\\'
# Button to select the console
SELECT_CONSOLE = '/'
