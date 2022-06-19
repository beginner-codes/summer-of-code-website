import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.status import HTTP_401_UNAUTHORIZED

from soc.context import inject
from soc.controllers.authentication import AuthenticationSettings, AuthTokenDict


def auth_scheme(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="authenticate")),
    settings=inject(AuthenticationSettings),
) -> AuthTokenDict:
    try:
        data = jwt.decode(token, settings.jwt.private_key, settings.jwt.algorithm)
    except jwt.exceptions.DecodeError:
        data = {}

    if data.get("user_id") is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return data
