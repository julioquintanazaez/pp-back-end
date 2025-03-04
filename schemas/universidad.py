from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Universidad(BaseModel):	
	universidad_nombre : str
	universidad_siglas : str
	universidad_tec : str
	universidad_transp : bool 	
	universidad_teletrab : bool
			
	class Config:
		from_attributes = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Universidad_InDB(Universidad):	
	id_universidad : str
