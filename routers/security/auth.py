from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session

from schemas.token import Token
from security.auth import create_access_token, authenticate_user, get_current_active_user, get_current_user
from db.database import get_db
from schemas.user import User_InDB, User_Record

from core.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                    db: Session = Depends(get_db)):
	user = authenticate_user(form_data.username, form_data.password, db)
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"},
		)
	access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
	access_token = create_access_token(
		data={"sub": user.usuario, "scopes": user.role},   #form_data.scopes
		expires_delta=access_token_expires
	)
	return {"detail": "Ok", "access_token": access_token, "token_type": "Bearer"}

@router.get("/users/me")
async def read_users_me(current_user: Annotated[User_InDB, Depends(get_current_user)]):
	return current_user

@router.get("/get_restricted_user")
async def get_restricted_user(current_user: Annotated[User_InDB, Depends(get_current_active_user)]):
    return current_user
	
@router.get("/get_authenticated_admin_resources")
async def get_authenticated_admin_resources(current_user: Annotated[User_InDB, Security(get_current_active_user, scopes=["profesor"])]):
    return current_user
	
@router.get("/get_authenticated_edition_resources")
async def get_authenticated_edition_resources(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["cliente"])]):
    return current_user
	
