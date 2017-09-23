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
    header = "Choose a map:"

    option_number = "{number:02}"

    input = "Select option: "

class Play(object):
    """Strings relating to the bulk of playing the game."""
    move = 'Move: '
    variable_set = '{variable} is now {value}'
    variable_get = '{variable} has value {value}'
    variable_get_failed = 'variable {variable} could not be found'
    debug_not_enabled = 'Debug mode must be enabled to use this command: \debug True'


class Help(object):
    """Strings relating to using the help command."""
    header = "Commands: (prefix non-movment commands with '\\')"
    debug_header = "Debug commands:"
    movement = 'Movement'
    movement_text = 'Use WASDRF to move.'