class Sep(object):
    """A string that is repeated to separate parts of the output."""
    sep = chr(9472)
    vert_sep = chr(9474)
    udlr_sep = chr(9532)
    udl_sep  = chr(9508)
    udr_sep  = chr(9500)
    ulr_sep  = chr(9524)
    dlr_sep  = chr(9516)
    ud_sep   = vert_sep
    ul_sep   = chr(9496)
    dl_sep   = chr(9488)
    ur_sep   = chr(9492)
    dr_sep   = chr(9484)
    lr_sep   = sep

class MapSelect(object):
    """Strings relating to the selecting of a map."""
    title = "Choose a map:"

    headers = ['Code', 'Name']

    option_number = "{number:02}"

    input = "Select code: "

class Play(object):
    """Strings relating to the bulk of playing the game."""
    variable_set = '{variable} is now {value}'
    variable_get = '{variable} has value {value}'
    variable_get_failed = 'variable {variable} could not be found'
    debug_not_enabled = 'Debug mode must be enabled to use this command: \debug True'
    # The message for input that could not be made sense of.
    INVALID_INPUT = 'Invalid input, please try again. Type \'\help\' for help.'

class Help(object):
    """Strings relating to using the help command."""
    header = "Commands: (prefix non-movment commands with '\\')"
    debug_header = "Debug commands:"
    movement = 'Movement'
    movement_text = 'Use WASDRF to move.'


class Data(object):
    """Strings relating to external data, like choosing maps."""
    class Exceptions(object):
        no_map_name = "Map with name {map_name} does not exist."
        no_entry = "Required field {entry} cannot be found on map {map_name}."
        misconfigured_map_data = "Map data not formatted correctly on map {map_name}."
