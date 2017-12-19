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
    BAD_TILE_GEOMETRY = 'Cannot interpret geometry "{geometry}".'
    # Listeners
    NO_LISTENER = 'No listener enabled.'
    INVALID_LISTENER_REMOVAL = 'Tried to remove listener "{listener}", which is not the currently enabled listener.'
    # Moving the player
    INVALID_FORCE_MOVE = 'Received an invalid force move command.'
    INVALID_INPUT_TYPE = 'Unexpected input type "{input}"'
    # Appearance
    NO_APPEARANCE_LOOKUP = 'No appearance lookup passed on tile initialisation, despite tile having multiple appearances.'


### Internal Strings ###
# These are only used internally, and are just put here to keep them consistent throughout the program.

# Used in determining stair adjacency.
class StairAdjacency(tools.Container):
    VERTICAL_UP = 'vert_up'
    VERTICAL_DOWN = 'vert_down'

# Movement commands for the player
class Move(tools.Container):
    DOWN = 'down'
    UP = 'up'
    LEFT = 'left'
    RIGHT = 'right'

# Other commands for the player
class Action(tools.Container):
    VERTICAL_UP = 'vert_up'
    VERTICAL_DOWN = 'vert_down'

# Menus
class Menus(tools.Container):
    MAIN_MENU = 'main_menu'
    MAP_SELECT = 'map_select'
    OPTIONS = 'options'
    GAME_START = 'game_start'  # Not a menu; special value to indicate that the main game should be started

# Input types
class InputTypes(tools.Container):
    MENU = 'menu'
    ACTION = 'action'
    NO_INPUT = 'no_input'

# Defines alignments when placing interface elements
class Alignment(tools.Container):
    LEFT = 'left'
    RIGHT = 'right'
    TOP = 'top'
    BOTTOM = 'bottom'
    CENTER = 'center'

# The rotations for tiles
class TileRotation(tools.Container):
    DOWN = 'down'
    UP = 'up'
    LEFT = 'left'
    RIGHT = 'right'

class Geometry(tools.Container):
    ANGLED = 'angled'
    CONCAVE = 'concave'
    CONVEX = 'convex'
    DOUBLE_CONCAVE = 'doub_conc'
    DOUBLE_CONVEX = 'doub_conv'
    CIRCLE = 'circle'
    SQUARE = 'square'
