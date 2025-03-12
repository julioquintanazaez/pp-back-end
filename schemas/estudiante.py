from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Estudiante_Record(BaseModel):
	est_trabajo : bool  
	est_becado : bool  
	est_posibilidad_economica : str 
	est_pos_tecnica_escuela : str
	est_pos_tecnica_hogar : str
	est_trab_remoto : bool	

	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	
		
class EstudianteAdd(Estudiante_Record):
	est_entidad_id : str	
	user_estudiante_id : str

class Estudiante_InDB(EstudianteAdd):	
	id_estudiante : str	
	est_ocupado: Union[bool, None] = False

class Estudiante_Activo(BaseModel):	
	est_ocupado: bool