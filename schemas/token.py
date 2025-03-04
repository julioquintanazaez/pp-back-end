from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
	usuario: Union[str, None] = None
	scopes: List[str] = []	