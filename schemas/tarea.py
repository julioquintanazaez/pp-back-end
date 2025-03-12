from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Tarea_Record(BaseModel):		
	tarea_descripcion : str 
	tarea_tipo : str
	tarea_fecha_inicio : date
	tarea_fecha_fin : date
	tarea_complejidad_estimada : str
	tarea_participantes : int #N�mero de miembros en el equipo
	
	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	

class TareaAdd(Tarea_Record):		
	tarea_estudiante_id : str
	tarea_conc_id : str
	
class Tarea_InDB(TareaAdd):	
	id_tarea : str	
	tarea_asignada : Union[str, None] = True
	tarea_activa : Union[str, None] = True
	tarea_evaluacion : Union[str, None] = None
	tarea_evaluacion_pred : Union[str, None] = None
	
class Tarea_Eval(BaseModel):
	tarea_evaluacion : str
