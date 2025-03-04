from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Concertacion_Tema(BaseModel):
	conc_tema : str
	conc_descripcion : str
	conc_valoracion_prof : str
	conc_valoracion_cliente : str 
	conc_complejidad : str #Alta, Baja, Media
	conc_actores_externos : int
	conc_profesor_id : str   
	conc_cliente_id : str 
	
	class Config:
		from_attributes = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Concertacion_Tema_InDB(Concertacion_Tema):
	id_conc_tema : str
	conc_activa : bool
	conc_evaluacion : Union[str, None] = None
	conc_evaluacion_pred : Union[str, None] = None

class Concertacion_Tema_Eval(BaseModel):
	conc_evaluacion : str #Positiva, Ngativa, Mejorable
	
class Concertacion_Tema_Activate(BaseModel):
	conc_activa : bool
	
class Concertacion_Tema_UPD(BaseModel):
	conc_tema : str
	conc_descripcion : str
	conc_valoracion_prof : str
	conc_valoracion_cliente : str 
	conc_complejidad : str #Alta, Baja, Media
	conc_actores_externos : int
	
class Concertacion_Tema_UPD_Actores(BaseModel):
	conc_profesor_id : str   
	conc_cliente_id : str 
