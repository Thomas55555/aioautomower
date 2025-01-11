"""Models for Husqvarna Authentication API."""

from dataclasses import dataclass

from mashumaro import DataClassDictMixin


@dataclass
class User(DataClassDictMixin):
    """The user details of the JWT."""

    first_name: str
    last_name: str
    custom_attributes: dict[str, str]
    customer_id: str


@dataclass
class JWT(DataClassDictMixin):
    """The content of the JWT."""

    jti: str
    iss: str
    roles: list[str]
    groups: list[str]
    scopes: list[str]
    scope: str
    client_id: str
    customer_id: str
    user: User
    iat: int
    exp: int
    sub: str
