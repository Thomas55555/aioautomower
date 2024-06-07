"""Library for exceptions using the Husqvarna Automower API."""


class HusqvarnaAutomowerException(Exception):
    """Base class for all client exceptions."""


class ApiException(HusqvarnaAutomowerException):
    """Raised during problems talking to the API."""


class AuthException(HusqvarnaAutomowerException):
    """Raised due to auth problems talking to API."""


class InvalidSyncTokenException(HusqvarnaAutomowerException):
    """Raised when the sync token is invalid."""


class ApiBadRequestException(HusqvarnaAutomowerException):
    """Raised due sending a Rest command resulting in a bad request."""


class ApiForbiddenException(HusqvarnaAutomowerException):
    """Raised due to permission errors talking to API."""


class ApiUnauthorizedException(HusqvarnaAutomowerException):
    """Raised occasionally, mustn't harm the connection."""


class NoDataAvailableException(HusqvarnaAutomowerException):
    """Raised due updating data, when no data is available."""


class TimeoutException(HusqvarnaAutomowerException):
    """Raised due connecting the websocket."""


class HusqvarnaWSServerHandshakeError(HusqvarnaAutomowerException):
    """Raised due connecting the websocket if server not available."""
