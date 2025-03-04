from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Profesor(BaseModel):
	prf_genero : str 
	prf_estado_civil : str  #Soltero, Casado, Divorciado, Viudo
	prf_numero_empleos : int 
	prf_hijos : bool
	prf_pos_tecnica_trabajo : str
	prf_pos_tecnica_hogar : str
	prf_trab_remoto : bool
	prf_cargo : bool
	prf_categoria_docente : str #Instructor, Auxiliar, Asistente, Titular
	prf_categoria_cientifica : str  #Ingeniero, Licenciado, Master, Doctor, Tecnico
	prf_experiencia_practicas : bool  
	prf_numero_est_atendidos : int  #Numero de estudiantes atendidos en el pasado
	prf_entidad_id : str 
	user_profesor_id : str
				
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Profesor_InDB(Profesor):	
	id_profesor : str	
	
class Profesor_UPD(BaseModel):
	prf_genero : str 
	prf_estado_civil : str  #Soltero, Casado, Divorciado, Viudo
	prf_numero_empleos : int 
	prf_hijos : bool
	prf_pos_tecnica_trabajo : str
	prf_pos_tecnica_hogar : str
	prf_trab_remoto : bool
	prf_cargo : bool
	prf_categoria_docente : str #Instructor, Auxiliar, Asistente, Titular
	prf_categoria_cientifica : str  #Ingeniero, Licenciado, Master, Doctor, Tecnico
	prf_experiencia_practicas : bool  
	prf_numero_est_atendidos : int  #Numero de estudiantes atendidos en el pasado
	