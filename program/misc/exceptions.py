# Okay exceptions; may be raised during expected usage of the game.
class BaseQuitException(Exception):
    """Base exception for all exceptions involving leaving the current game."""


class QuitException(BaseQuitException):
    """Indicates the the main menu screen should be returned to."""


class ResetException(QuitException):
    """Indicates that the whole instance should start over from scratch."""


class CloseException(BaseQuitException):
    """Indicates that the whole application should be closed."""


class SaveException(Exception):
    """Indicates that the map editor cannot save the file (e.g. due to not having a map name.)"""


class MapLoadException(Exception):
    """Indicates that the given string cannot be deserialised into a tile."""


# Bad exceptions; probably raised because of code errors

class BaseGameException(Exception):
    """Base exception for all bad exceptions raised during the game's runtime."""


class ProgrammingException(BaseGameException):
    """Raised due to an internal problems, likely because of incorrect code."""


class SdlException(BaseGameException):
    """Raised due to a problem from SDL."""


class ListenerRemovalException(BaseGameException):
    """Raised due to not being able to correctly remove a listener. Can mean that a listener added with add_listener
    was not properly removed with remove_listener once it was finished with."""

