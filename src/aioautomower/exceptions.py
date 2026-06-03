"""Library for Exception using the Husqvarna Automower API."""


class HusqvarnaAutomowerError(Exception):
    """Base class for all client Errors."""


class ApiError(HusqvarnaAutomowerError):
    """Raised during problems talking to the API."""


class FeatureNotSupportedError(HusqvarnaAutomowerError):
    """Raised when the feature is not supported by the mower."""


class WorkAreasDifferentError(HusqvarnaAutomowerError):
    """Raised when the work areas for setting the calendar are different."""


class AuthError(HusqvarnaAutomowerError):
    """Raised due to auth problems talking to API."""


class InvalidSyncTokenError(HusqvarnaAutomowerError):
    """Raised when the sync token is invalid."""


class ApiBadRequestError(HusqvarnaAutomowerError):
    """Raised due sending a Rest command resulting in a bad request."""


class ApiForbiddenError(HusqvarnaAutomowerError):
    """Raised due to permission errors talking to API."""


class ApiUnauthorizedError(HusqvarnaAutomowerError):
    """Raised occasionally, mustn't harm the connection."""


class NoDataAvailableError(HusqvarnaAutomowerError):
    """Raised due updating data, when no data is available."""


class HusqvarnaTimeoutError(HusqvarnaAutomowerError):
    """Raised due connecting the websocket."""


class HusqvarnaWSServerHandshakeError(HusqvarnaAutomowerError):
    """Raised due connecting the websocket if server not available."""


class HusqvarnaWSClientError(HusqvarnaAutomowerError):
    """Raised due connecting the websocket."""
