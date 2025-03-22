from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Security, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import ValidationError
from typing_extensions import Annotated
from typing import Union
from db.database import get_db
from core import config
from models.data import User
from schemas.token import TokenData
from schemas.user import User_InDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
	tokenUrl="token",
	scopes={"admin": "Add, edit and delete information.", "profesor": "Create and read information.", "cliente": "Create and read information.", "estudiante": "Create and read information."}
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, usuario: str):
	db_user = db.query(User).filter(User.usuario == usuario).first()	
	if db_user is not None:
		return db_user 

def authenticate_user(usuario: str, password: str,  db: Session = Depends(get_db)):
    user = get_user(db, usuario)
    if not user:
        return False
    if not verify_password(password, user.hashed_password): #secret
        return False
    return user
	
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30) #Si no se pasa un valor por usuario
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt
	
async def get_current_user(
			security_scopes: SecurityScopes, 
			token: Annotated[str, Depends(oauth2_scheme)],
			db: Session = Depends(get_db)):
	if security_scopes.scopes:
		authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
	else:
		authenticate_value = "Bearer"
		
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Imposible validar credenciales para el usuario",
		headers={"WWW-Authenticate": "Bearer"},
	)

	try:
		payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
		usuario: str = payload.get("sub")
		if usuario is None:
			raise credentials_exception			
		token_scopes = payload.get("scopes", [])
		token_data = TokenData(scopes=token_scopes, usuario=usuario)

	except (JWTError, ValidationError):
		raise credentials_exception

	except JWTError:
		raise credentials_exception
	
	user = get_user(db, usuario=token_data.usuario)

	if user is None:
		raise credentials_exception
		
	for user_scope in security_scopes.scopes:
		if user_scope not in token_data.scopes:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Not enough permissions",
				headers={"WWW-Authenticate": authenticate_value},
			)
			
	return user
	
async def get_current_active_user(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])]):  
	return current_user


	