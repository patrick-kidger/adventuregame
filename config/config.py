import Tools as tools


### Gameplay Settings ###

# Default speed of all entities
DEFAULT_ENTITY_SPEED = 2.0

# How many ticks of physics should be done each second.
PHYSICS_FRAMERATE = 120
# FPS cap
RENDER_FRAMERATE = 60

# How many physics ticks it should take to fall through one z-level
FALL_TICKS = 15

### Menu Settings ###

# How many pixels to scroll in menus when using the scroll wheel
SCROLL_SPEED = 40

### Application Settings ###

WINDOW_NAME = 'Maze Game'

# The file extension for map files
MAP_FILE_EXTENSION = 'map'

# The name of the folder containing the map data
MAP_FOLDER = 'data/map_data'

# The names of the folders containing the interface / tile / entity images respectively
INTERFACE_FOLDER = 'images/interface'
TILE_FOLDER = 'images/tiles'
ENTITY_FOLDER = 'images/entities'


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

class Move(tools.Container):
    """All valid inputs for moving the player character."""
    DOWN = 's'
    UP = 'w'
    LEFT = 'a'
    RIGHT = 'd'

class Action(tools.Container):
    """All valid inputs for commanding (other than moving) the player character."""
    VERTICAL_UP = 'r'
    VERTICAL_DOWN = 'f'

class DebugCommands(tools.Container):
    """All valid commands in the console"""
    DEBUG = 'debug'
    CLEAR = 'clear'
    HELP = 'help'
    NOCLIP = 'noclip'
    FLY = 'fly'
    GHOST = 'ghost'
    SETSPEED = 'setspeed'
    GET = 'get'
    QUIT = 'quit'  # Quits back to menus
    EXIT = 'exit'   # Quits back to menus
    CLOSE = 'close'  # Closes the whole application
    CURRENT_TILE = 'currenttile'


# How long a key should be held down for to start generating repeat keypresses.
KEY_REPEAT_DELAY = 100
# How often a key generates repeat keypresses (once it's been held down long enough to generate them).
KEY_REPEAT = 30

# Button to toggle the console
OPEN_CONSOLE = '\\'
# Button to (de)select the console if it's open
SELECT_CONSOLE = '/'
# How many of its past commands the console should remember when using the arrow keys to copy past commands
CONSOLE_MEMORY_SIZE = 20
# How long each line should be in the console before getting wrapped
CONSOLE_LINE_LENGTH = 130
# What the prompt should be in the console
CONSOLE_PROMPT = '> '
