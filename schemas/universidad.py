from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class UniversidadAdd(BaseModel):	
	universidad_nombre : str
	universidad_siglas : str
	universidad_tec : str
	universidad_transp : bool 	
	universidad_teletrab : bool
			
	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	
		
class Universidad_InDB(UniversidadAdd):	
	id_universidad : str
