from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 
from uuid import UUID

class Cliente_Record(BaseModel):
	cli_numero_empleos : int
	cli_pos_tecnica_trabajo : str
	cli_pos_tecnica_hogar : str
	cli_cargo : bool
	cli_trab_remoto : bool
	cli_categoria_docente : str #Instructor, Auxiliar, Asistente, Titular
	cli_categoria_cientifica : str #Ingeniero, Licenciado, Master, Doctor, Tecnico
	cli_experiencia_practicas : bool  
	cli_numero_est_atendidos : int  #Numero de estudiantes atendidos en el pasado

	class Config:
		from_attributes = True
		populate_by_name = True
		arbitrary_types_allowed = True	

class ClienteAdd(Cliente_Record):
	cli_centro_id : str
	user_cliente_id : str

class Cliente_InDB(ClienteAdd):	
	id_cliente : str	

class ClienteSchema(BaseModel):
	id_cliente: UUID
	cli_numero_empleos : int
	cli_pos_tecnica_trabajo : str
	cli_pos_tecnica_hogar : str
	cli_cargo : bool
	cli_trab_remoto : bool
	cli_categoria_docente : str 
	cli_categoria_cientifica : str 
	cli_experiencia_practicas : bool  
	cli_numero_est_atendidos : int  
	usuario_id: UUID
	ci: str
	nombre: str
	primer_appellido: str
	segundo_appellido: str
	email: str

	class Config:
		from_attributes = True  # Permite que Pydantic trabaje con objetos ORM


	