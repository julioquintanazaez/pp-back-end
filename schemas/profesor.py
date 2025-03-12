from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Profesor_Record(BaseModel):
	prf_numero_empleos : int 
	prf_pos_tecnica_trabajo : str
	prf_pos_tecnica_hogar : str
	prf_trab_remoto : bool
	prf_cargo : bool
	prf_categoria_docente : str #Instructor, Auxiliar, Asistente, Titular
	prf_categoria_cientifica : str  #Ingeniero, Licenciado, Master, Doctor, Tecnico
	prf_experiencia_practicas : bool  
	prf_numero_est_atendidos : int  #Numero de estudiantes atendidos en el pasado

	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True
			
class ProfesorAdd(Profesor_Record):
	prf_entidad_id : str 
	user_profesor_id : str
		
class Profesor_InDB(ProfesorAdd):	
	id_profesor : str	
	

	