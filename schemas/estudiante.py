from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Estudiante(BaseModel):
	est_genero : str  
	est_estado_civil : str  #Soltero, Casado, Divorciado, Viudo
	est_trabajo : bool  
	est_becado : bool  
	est_hijos : bool  
	est_posibilidad_economica : str 
	est_pos_tecnica_escuela : str
	est_pos_tecnica_hogar : str
	est_trab_remoto : bool
	est_entidad_id : str	
	user_estudiante_id : str

	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Estudiante_UPD(BaseModel):
	est_genero : str  
	est_estado_civil : str  #Soltero, Casado, Divorciado, Viudo
	est_trabajo : bool  
	est_becado : bool  
	est_hijos : bool  
	est_posibilidad_economica : str 
	est_pos_tecnica_escuela : str
	est_pos_tecnica_hogar : str
	est_trab_remoto : bool	

class Estudiante_InDB(Estudiante):	
	id_estudiante : str	