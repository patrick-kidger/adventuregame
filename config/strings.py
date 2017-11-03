import Tools as tools


class Sep(tools.Container):
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

class MapSelect(tools.Container):
    """Strings relating to the selecting of a map."""
    TITLE = "Choose a map:"
    HEADERS = ['Code', 'Name']
    OPTION_NUMBER = "{number:02}"
    PROMPT = "Select code: "
    SELECT_MAP = 'Select map'

class Play(tools.Container):
    """Strings relating to the bulk of playing the game."""
    VARIABLE_SET = '{variable} is now {value}'
    VARIABLE_GET = '{variable} has value {value}'
    VARIABLE_GET_FAILED = 'variable {variable} could not be found'
    DEBUG_NOT_ENABLED = 'Debug mode must be enabled to use this command: debug True'
    # The message for input that could not be made sense of.
    INVALID_INPUT = 'Invalid input, please try again. Type \'help\' for help.'

class Help(tools.Container):
    """Strings relating to using the help command."""
    HEADER = "Commands:"
    DEBUG_HEADER = "Debug commands:"
