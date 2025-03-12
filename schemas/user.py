from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class User_Read(BaseModel):	
	email: Union[EmailStr, None] = None
	ci : Union[str, None] = None
	nombre : Union[str, None] = None	
	primer_appellido : Union[str, None] = None  
	segundo_appellido : Union[str, None] = None 
	genero : Union[str, None] = None 
	estado_civil : Union[str, None] = None 
	hijos : Union[bool, None] = None 
	role: List[str] = ["usuario"]
	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	
	
class User_List(User_Read):	
	usuario: str	

class User_Record(User_List):
	hashed_password: str
	
class User_InDB(User_Record):
	id: str
	deshabilitado: Union[bool, None] = None	

class User_Activate(BaseModel):	
	deshabilitado: Union[bool, None] = None
		
class User_ResetPassword(BaseModel):
	actualpassword: str
	newpassword: str