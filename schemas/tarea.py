from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Asignacion_Tarea(BaseModel):		
	asg_descripcion : str 
	asg_fecha_inicio : date
	asg_fecha_fin : date
	asg_complejidad_estimada : str
	asg_participantes : int #N�mero de miembros en el equipo
	asg_tipo_tarea_id : str
	asg_estudiante_id : str
	asg_conc_id : str

	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
	
class Asignacion_Tarea_InDB(Asignacion_Tarea):	
	id_asignacion : str	
	asg_asignada : bool	
	asg_activa : bool
	asg_evaluacion : Union[str, None] = None
	asg_evaluacion_pred : Union[str, None] = None
	

class Asignacion_Tarea_Eval(BaseModel):
	asg_evaluacion : str
	
class Asignacion_Tarea_UPD(BaseModel):		
	asg_descripcion : str 
	asg_fecha_inicio : date
	asg_fecha_fin : date
	asg_complejidad_estimada : str
	asg_participantes : int #N�mero de miembros en el equipo
	
class Asignacion_Tarea_UPD_Tipo(BaseModel):	
	asg_tipo_tarea_id : str
	
class Asignacion_Tarea_PUD_Gestor(BaseModel):	
	asg_estudiante_id : str
	
class Asignacion_Tarea_Activate(BaseModel):
	asg_activa : bool
	