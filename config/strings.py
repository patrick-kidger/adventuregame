import Tools as tools


class Exceptions(tools.Container):
    """The error messages in exceptions raised by the program."""

    # Menu navigation
    MENU_MOVE_WRONG = ("MENU event given - i.e. a submit or back element was used - without any of those elements "
                       "having registered interactions, or with more than one of those elements having registered "
                       "interactions.")
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
    # Appearance
    NO_APPEARANCE_LOOKUP = 'No appearance lookup set, despite tile having multiple appearances.'
    NON_SQUARE_TILE = 'Tile images must be squares.'
    # Map Editor
    NO_START_POS = 'The map needs a start position.'
    NO_MAP_SAVE_NAME = 'Need a name for the map.'
    NO_TILES = 'No tiles have been placed.'
    BAD_START_POS = 'The start position is not over a tile.'
    CANNOT_SAVE_FILE = 'Could not save the file due to a system error. Do you have permission to write to this file?'
    # SDL
    SUBSURFACE_OFFSET = 'Cannot set the offset of a subsurface or a cutout.'


class Sep(tools.Container):
    """A string that is repeated to separate parts of text output."""
    SEP      = chr(9472)
    VERT_SEP = chr(9474)
    UDLR_SEP = chr(9532)
    UDL_SEP  = chr(9508)
    UDR_SEP  = chr(9500)
    ULR_SEP  = chr(9524)
    DLR_SEP  = chr(9516)
    UD_SEP   = VERT_SEP
    UL_SEP   = chr(9496)
    DL_SEP   = chr(9488)
    UR_SEP   = chr(9492)
    DR_SEP   = chr(9484)
    LR_SEP   = SEP


class _Menus(tools.Container):
    MAIN_MENU = 'Main menu'


class MainMenu(_Menus):
    """Strings relating to the main menu."""
    START = 'Start'
    OPTIONS = 'Options'


class MapSelectMenu(_Menus):
    """Strings relating to the selecting of a map."""
    TITLE = "Choose a map:"
    HEADERS = ['Code', 'Name']
    OPTION_NUMBER = "{number:02}"
    PROMPT = "Select code: "
    SELECT_MAP = 'Select map'


class Debug(tools.Container):
    """Strings relating to using debug commands."""
    VARIABLE_SET = '{variable} is now {value}'
    VARIABLE_SET_FAILED = '"{value}" could not be interpreted as type {variable_type}'
    VARIABLE_GET = '{variable} has value {value}'
    VARIABLE_GET_FAILED = 'variable {variable} could not be found'
    DEBUG_NOT_ENABLED = 'Debug mode must be enabled to use this command: debug True'
    INVALID_INPUT = 'Invalid input, please try again. Type \'help\' for help.'
    HEADER = "Commands:"
    DEBUG_HEADER = "Debug commands:"


class MapEditor(tools.Container):
    WINDOW_TITLE = 'Game Map Editor'
    QUIT_TITLE = 'Quit'
    QUIT_QUESTION = 'Do you want to quit? Unsaved data will be lost.'
    NEW = 'New'
    SAVE = 'Save'
    OPEN = 'Open'
    OPEN_TITLE = 'Open file'
    NEW_TITLE = 'Clear map?'
    NEW_MESSAGE = 'Clear all map data? All unsaved data will be lost.'
    MAP_NAME_PROMPT = 'Map name: '
    CURRENT_Z_LEVEL = "Current z level: "
    CHANGE_Z_LEVEL = 'Change z level:'
    SET_START_POS = 'Set starting position'
    DELETE_TILE = 'Delete tile'
    BAD_LOAD_TITLE = 'Could not load file'
    BAD_LOAD_MESSAGE = 'Could not load file. File may be missing or corrupted.'
    CANNOT_SAVE = 'Cannot save'
    SETTING_CUBOID = 'Setting cuboid'
