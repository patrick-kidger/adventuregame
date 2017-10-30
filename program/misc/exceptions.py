class BaseGameException(Exception):
    """Base exception for all exceptions raised during the game's runtime."""


class CloseException(BaseGameException):
    """Indicates that the whole game should be closed."""


class ProgrammingException(BaseGameException):
    """Raised due to an internal problems, likely because of incorrect code."""


class ListenerRemovalException(BaseGameException):
    """Raised due to not being able to correctly remove a listener. Can mean that a listener added with add_listener
    was not properly removed with remove_listener once it was finished with."""


class NoTileDefinitionException(BaseGameException):
    """Raised when interpreting a map's tile data, and one of the characters does not correspond to any known tile
    definition."""
