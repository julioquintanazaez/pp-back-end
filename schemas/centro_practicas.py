from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 


class Centro_Practicas(BaseModel):	
	centro_nombre : str
	centro_siglas : str
	centro_tec : str
	centro_transp : bool
	centro_experiencia : bool 
	centro_teletrab : bool
			
	class Config:
		from_attributes = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Centro_Practicas_InDB(Centro_Practicas):	
	id_centro : str	
	