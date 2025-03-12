from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Concertacion_Record(BaseModel):
	conc_tema : str
	conc_descripcion : str
	conc_valoracion_prof : str
	conc_valoracion_cliente : str 
	conc_complejidad : str #Alta, Baja, Media
	conc_actores_externos : int
	conc_activa : bool
		
	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	

class ConcertacionAdd(Concertacion_Record):
	conc_profesor_id : str   
	conc_cliente_id : str 
		
class Concertacion_InDB(ConcertacionAdd):
	id_conc_tema : str	
	conc_evaluacion : Union[str, None] = None
	conc_evaluacion_pred : Union[str, None] = None

class Concertacion_Eval(BaseModel):
	conc_evaluacion : str #Positiva, Ngativa, Mejorable
	
class Concertacion_Activate(BaseModel):
	conc_activa : bool
	
class Concertacion_Actores(BaseModel):
	conc_profesor_id : str   
	conc_cliente_id : str 
