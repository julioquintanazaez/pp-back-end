from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class Cliente_Read(BaseModel):
	cli_genero : str
	cli_estado_civil : str  #Soltero, Casado, Divorciado, Viudo
	cli_numero_empleos : int
	cli_hijos : bool 
	cli_pos_tecnica_trabajo : str
	cli_pos_tecnica_hogar : str
	cli_cargo : bool
	cli_trab_remoto : bool
	cli_categoria_docente : str #Instructor, Auxiliar, Asistente, Titular
	cli_categoria_cientifica : str #Ingeniero, Licenciado, Master, Doctor, Tecnico
	cli_experiencia_practicas : bool  
	cli_numero_est_atendidos : int  #Numero de estudiantes atendidos en el pasado

class Cliente_Record(Cliente_Read):
	cli_entidad_id : str
	user_cliente_id : str

	class Config:
		from_attributes = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
	
class Cliente_InDB(Cliente_Record):	
	id_cliente : str	


	