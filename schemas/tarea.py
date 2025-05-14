from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 
from uuid import UUID

class Tarea_Record(BaseModel):		
	tarea_descripcion : str 
	tarea_tipo : str
	tarea_fecha_inicio : date
	tarea_fecha_fin : date
	tarea_complejidad_estimada : str
	tarea_participantes : int 
	
	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	

class TareaAdd(Tarea_Record):		
	concertacion_tarea_id : str
	
class Tarea_InDB(TareaAdd):	
	id_tarea : str	
	tarea_asignada : Union[str, None] = True
	tarea_activa : Union[str, None] = True
	tarea_evaluacion : Union[str, None] = None
	tarea_evaluacion_pred : Union[str, None] = None
	
class Tarea_Eval(BaseModel):
	tarea_evaluacion : str


class TareaSchema(BaseModel):
	id_conc_tema: UUID
	conc_tema: str
	conc_cliente_id: UUID
	conc_profesor_id: UUID
	id_profesor: UUID	
	prf_user_id: UUID
	prf_nombre: str
	prf_primer_appellido: str
	prf_segundo_appellido: str
	id_cliente: UUID
	cli_user_id: UUID
	cli_nombre: str
	cli_primer_appellido: str
	cli_segundo_appellido: str
	id_estudiante: UUID
	est_user_id: UUID
	est_nombre: str
	est_primer_appellido: str
	est_segundo_appellido: str
	id_tarea: UUID
	concertacion_tarea_id: UUID
	tarea_activa: bool
	tarea_asignada: bool
	tarea_complejidad_estimada: str
	tarea_descripcion: str
	tarea_evaluacion: str
	tarea_evaluacion_pred: str
	tarea_fecha_fin: date
	tarea_fecha_inicio: date
	tarea_participantes: int
	tarea_tipo: str
	id_estudiante: UUID
	est_trabajo : bool
	est_becado : bool
	est_posibilidad_economica : str
	est_pos_tecnica_escuela : str
	est_pos_tecnica_hogar : str
	est_trab_remoto : bool 
	usuario_id: UUID
	ci: str
	nombre: str
	primer_appellido: str
	segundo_appellido: str
	email: str
	id_tarea: UUID
	tarea_tipo: str
	tarea_descripcion: str

	class Config:
		from_attributes = True  # Permite que Pydantic trabaje con objetos ORM