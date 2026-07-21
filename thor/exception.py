class ThorError(Exception):
    """Base exception for THOR."""
    pass


class BrokerError(ThorError):
    """Error while communicating with a broker."""
    pass


class AuthenticationError(BrokerError):
    """Authentication failed."""
    pass


class QueryError(BrokerError):
    """Invalid broker query."""
    pass


class ParsingError(BrokerError):
    """Unable to parse broker response."""
    pass

class ServiceError(ThorError):
    """Scientific service failed."""
    pass