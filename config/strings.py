class Sep(object):
    """A string that is repeated to separate parts of the output."""
    SEP = chr(9472)
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

class MapSelect(object):
    """Strings relating to the selecting of a map."""
    TITLE = "Choose a map:"
    HEADERS = ['Code', 'Name']
    OPTION_NUMBER = "{number:02}"
    PROMPT = "Select code: "
    class Exceptions(object):
        NO_TILE_DEFINITION = 'Cannot find a tile with definition "{definition}".'

class Play(object):
    """Strings relating to the bulk of playing the game."""
    VARIABLE_SET = '{variable} is now {value}'
    VARIABLE_GET = '{variable} has value {value}'
    VARIABLE_GET_FAILED = 'variable {variable} could not be found'
    DEBUG_NOT_ENABLED = 'Debug mode must be enabled to use this command: \debug True'
    # The message for input that could not be made sense of.
    INVALID_INPUT = 'Invalid input, please try again. Type \'help\' for help.'
    class Exceptions(object):
        INVALID_DIRECTION = 'Unexpected direction "{direction}"'
        INVALID_FORCE_MOVE = 'Received an invalid force move command.'
        INVALID_INPUT_TYPE = 'Unexpected input type "{input}"'

class Input(object):
    class Exceptions(object):
        NO_LISTENER = 'No listener enabled.'
        INVALID_LISTENER_REMOVAL = 'Tried to remove listener "{listener}", which is not the currently enabled listener.'

class Help(object):
    """Strings relating to using the help command."""
    HEADER = "Commands: (prefix non-movment commands with '\\')"
    DEBUG_HEADER = "Debug commands:"
    MOVEMENT = 'Movement'
    MOVEMENT_TEXT = 'Use WASDRF to move.'

class Data(object):
    """Strings relating to external data, like choosing maps."""
    class Exceptions(object):
        NO_MAP_NAME = "Map with name {map_name} does not exist."
        NO_ENTRY = "Required field {entry} cannot be found on map {map_name}."
        MISCONFIGURED_MAP_DATA = "Map data not formatted correctly on map {map_name}."
