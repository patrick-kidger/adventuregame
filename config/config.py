import Tools as tools


### Settings ###

WINDOW_NAME = 'Maze Game'

# Pygame output options
SCREEN_SIZE = (800, 600)  # The overall size of the screen
DEBUG_SCREEN_SIZE = (800, 300)  # The size of the debug overlay
DEBUG_SCREEN_LOC = (0, 300)  # The location of the debug overlay on the main screen
GRAPHICS_SCREEN_SIZE = (800, 300)  # The size of the debug overlay
GRAPHICS_SCREEN_LOC = (0, 0)  # The location of the graphics overlay on hte main screen
SCREEN_BACKGROUND_COLOR = (255, 255, 255)  # White

# Debug overlay text options
FONT_NAME = "Monospace"
FONT_SIZE = 20
FONT_COLOR = (0, 0, 0)  # Black

# How long to wait at each state when skipping user input.
SLEEP_SKIP = 0.1  # In seconds!

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

# The special characters for walls, depending on the adjacency of other walls
class WallChars(tools.Container):
    UDLR = chr(9580)
    UDL =  chr(9571)
    UDR =  chr(9568)
    ULR =  chr(9577)
    DLR =  chr(9574)
    UD =   chr(9553)
    UL =   chr(9565)
    DL =   chr(9559)
    UR =   chr(9562)
    DR =   chr(9556)
    LR =   chr(9552)
    U = 'O'
    D = 'O'
    L = 'O'
    R = 'O'
    COLUMN = 'O'

# The character to represent the player.
PLAYER_DISPLAY = '@'

# The default character to display any entity.
ENTITY_DISPLAY = 'g'


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
    
class Input(Move):
    """All valid inputs in the console"""
    DEBUG = 'debug'
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

# Button to open up the console
ESCAPE_INPUT = '\\'


### Internal Strings ###
# These are only used internally, and are just put here to keep them consistent throughout the program.

# Names of overlays
class OverlayNames(tools.Container):
    DEBUG_NAME = 'debug'
    GAME_NAME = 'game'

# Used in determining wall adjacency.
class WallAdjacency(tools.Container):
    DOWN = 'down'
    UP = 'up'
    LEFT = 'left'
    RIGHT = 'right'

# Our different input states
class InputInterfaces(tools.Container):
    PLAY = 'play'
    SELECTMAP = 'selectmap'

# Playing the game
class Play(tools.Container):
    DOWN = 'down'
    UP = 'up'
    LEFT = 'left'
    RIGHT = 'right'
    VERTICAL_UP = 'vertical_up'
    VERTICAL_DOWN = 'vertical_down'
