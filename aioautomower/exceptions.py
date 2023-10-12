"""Library for exceptions using the Husqvarna Automower API."""


class HusqvarnaAAutomowerException(Exception):
    """Base class for all client exceptions."""


class ApiException(HusqvarnaAAutomowerException):
    """Raised during problems talking to the API."""


class AuthException(HusqvarnaAAutomowerException):
    """Raised due to auth problems talking to API."""


class InvalidSyncTokenException(HusqvarnaAAutomowerException):
    """Raised when the sync token is invalid."""


class ApiForbiddenException(HusqvarnaAAutomowerException):
    """Raised due to permission errors talking to API."""
