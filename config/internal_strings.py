import Tools as tools


### Internal Strings ###
# These are only used internally, and are just put here to keep them consistent throughout the program.

# Names of overlays
class OverlayNames(tools.Container):
    DEBUG = 'debug'
    GAME = 'game'

# Names of listeners
class ListenerNames(tools.Container):
    DEBUG = 'debug'
    GAME = 'game'

# Used in determining wall adjacency.
class WallAdjacency(tools.Container):
    DOWN = 'down'
    UP = 'up'
    LEFT = 'left'
    RIGHT = 'right'

# Playing the game
class Play(tools.Container):
    DOWN = 'down'
    UP = 'up'
    LEFT = 'left'
    RIGHT = 'right'
    VERTICAL_UP = 'vertical_up'
    VERTICAL_DOWN = 'vertical_down'

# Input types
class InputTypes(tools.Container):
    MOVEMENT = 'move'
    NO_INPUT = 'no_input'
    DEBUG = 'debug'
