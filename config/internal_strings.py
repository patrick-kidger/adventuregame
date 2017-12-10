import Tools as tools


class Exceptions(tools.Container):
    # Menu navigation
    MENU_MOVE_WRONG = "MENU event given - i.e. a submit or back element was used - without any of those" \
                                    " elements having registered interactions, or with more than one of those " \
                                    "elements having registered interactions."
    # Loading map data
    NO_MAP_NAME = "Map with name {map_name} does not exist."
    NO_ENTRY = "Required field {entry} cannot be found on map {map_name}."
    MISCONFIGURED_MAP_DATA = "Map data not formatted correctly on map {map_name}."
    # Interpreting map data
    NO_TILE_DEFINITION = 'Cannot find a tile with definition "{definition}".'
    # Listeners
    NO_LISTENER = 'No listener enabled.'
    INVALID_LISTENER_REMOVAL = 'Tried to remove listener "{listener}", which is not the currently enabled listener.'
    # Moving the player
    INVALID_DIRECTION = 'Unexpected direction "{direction}"'
    INVALID_FORCE_MOVE = 'Received an invalid force move command.'
    INVALID_INPUT_TYPE = 'Unexpected input type "{input}"'


### Internal Strings ###
# These are only used internally, and are just put here to keep them consistent throughout the program.

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

# Menus
class Menus(tools.Container):
    MAIN_MENU = 'main_menu'
    MAP_SELECT = 'map_select'
    OPTIONS = 'options'
    GAME_START = 'game_start'  # Not a menu; special value to indicate that the main game should be started

# Input types
class InputTypes(tools.Container):
    MENU = 'menu'
    MOVEMENT = 'move'
    NO_INPUT = 'no_input'

# Defines alignments when placing interface elements
class Alignment(tools.Container):
    LEFT = 'left'
    RIGHT = 'right'
    TOP = 'top'
    BOTTOM = 'bottom'
    CENTER = 'center'
