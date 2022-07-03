from fastapi import Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from soc.context import create_app, inject
from soc.controllers.authentication import Authentication

api_app = create_app()


@api_app.post("/register")
async def register_user(
    data: OAuth2PasswordRequestForm = Depends(),
    email: str = Form(),
    auth=inject(Authentication),
):
    await auth.register_user(data.username, data.password, email)
    return {"detail": "User successfully registered"}


@api_app.post("/authenticate")
async def authenticate_user(
    data: OAuth2PasswordRequestForm = Depends(),
    auth: Authentication = inject(Authentication),
):
    user = await auth.authenticate_user(data.username, data.password)
    if user:
        token, _ = await auth.create_user_session(user)
        return {"access_token": token}
    else:
        raise HTTPException(403, "Invalid user")
