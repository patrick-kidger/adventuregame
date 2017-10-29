class BaseGameException(Exception):
    """Base exception for all exceptions raised during the game's runtime."""


class ProgrammingException(BaseGameException):
    """Raised due to an internal problems, likely because of incorrect code."""


class NoTileDefinitionException(BaseGameException):
    """Raised when interpreting a map's tile data, and one of the characters does not correspond to any known tile
    definition."""
