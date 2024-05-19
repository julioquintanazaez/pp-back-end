from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

class UserUPD(BaseModel):	
	email: Union[EmailStr, None] = None
	ci : Union[str, None] = None
	nombre : Union[str, None] = None	
	primer_appellido : Union[str, None] = None  
	segundo_appellido : Union[str, None] = None 
	role: List[str] = []
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class UserActivate(BaseModel):	
	disable: Union[bool, None] = None
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
	
class User(BaseModel):	
	username: str
	email: EmailStr
	ci : str
	nombre : str	
	primer_appellido : str  
	segundo_appellido : str 
	role: List[str] = []		
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	

class UserAdd(User):
	hashed_password: str
	
class UserInDB(UserAdd):
	id: str
	disable: Union[bool, None] = None
	
class UserPassword(BaseModel):
    hashed_password: str
	
class UserResetPassword(BaseModel):
	actualpassword: str
	newpassword: str

#-------------------------
#-------TOKEN-------------
#-------------------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
	username: Union[str, None] = None
	scopes: List[str] = []	

#-------------------------
#-----ENTIDAD ORIGEN------
#-------------------------
class Entidad_Origen(BaseModel):	
	org_nombre : str
	org_siglas : str
	org_nivel_tecnologico : str
	org_transporte : bool 	
	org_trab_remoto : bool
			
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Entidad_Origen_InDB(Entidad_Origen):	
	id_entidad_origen : str

#-------------------------
#-----ENTIDAD DESTINO-----
#-------------------------
class Entidad_Destino(BaseModel):	
	dest_nombre : str
	dest_siglas : str
	dest_nivel_tecnologico : str
	dest_transporte : bool
	dest_experiencia : bool 
	dest_trab_remoto : bool
			
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Entidad_Destino_InDB(Entidad_Destino):	
	id_entidad_destino : str	
	
#-------------------------
#-----  PROFESOR  --------
#-------------------------
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
	
#-------------------------
#----- ESTUDIANTE --------
#-------------------------
class Estudiante(BaseModel):
	est_genero : str  
	est_estado_civil : str  #Soltero, Casado, Divorciado, Viudo
	est_trabajo : bool  
	est_becado : bool  
	est_hijos : bool  
	est_posibilidad_economica : str 
	est_pos_tecnica_escuela : str
	est_pos_tecnica_hogar : str
	est_trab_remoto : bool
	est_entidad_id : str	
	user_estudiante_id : str

	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
		
class Estudiante_UPD(BaseModel):
	est_genero : str  
	est_estado_civil : str  #Soltero, Casado, Divorciado, Viudo
	est_trabajo : bool  
	est_becado : bool  
	est_hijos : bool  
	est_posibilidad_economica : str 
	est_pos_tecnica_escuela : str
	est_pos_tecnica_hogar : str
	est_trab_remoto : bool	

class Estudiante_InDB(Estudiante):	
	id_estudiante : str	
		
#-------------------------
#------  CLIENTE  --------
#-------------------------
class Cliente(BaseModel):
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
	cli_entidad_id : str
	user_cliente_id : str

	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
	
class Cliente_InDB(Cliente):	
	id_cliente : str	

class Cliente_UPD(BaseModel):
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
	
#-------------------------
#--- CONCERTACIÓN TEMA ---
#-------------------------
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
		orm_mode = True
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

#-------------------------
#-------  TAREA  ---------
#-------------------------
class Tipo_Tarea(BaseModel):	
	tarea_tipo_nombre : str 	

	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
	
class Tipo_Tarea_InDB(Tipo_Tarea):	
	id_tipo_tarea : str	

#-------------------------
#---- ASIGNACIÓN TAREA ---
#-------------------------
class Asignacion_Tarea(BaseModel):		
	asg_descripcion : str 
	asg_fecha_inicio : date
	asg_fecha_fin : date
	asg_complejidad_estimada : str
	asg_participantes : int #Número de miembros en el equipo
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
	asg_participantes : int #Número de miembros en el equipo
	
class Asignacion_Tarea_UPD_Tipo(BaseModel):	
	asg_tipo_tarea_id : str
	
class Asignacion_Tarea_PUD_Gestor(BaseModel):	
	asg_estudiante_id : str
	
class Asignacion_Tarea_Activate(BaseModel):
	asg_activa : bool
	
#-------------------------
#--- ACTIVIDADES TAREA ---
#-------------------------
class Actividades_Tarea_Est(BaseModel):		
	act_nombre : str
	act_est_memo : str
	id_asg_act : str	
	
class Actividades_Tarea_Prf(BaseModel):		
	act_nombre : str
	act_prof_memo : str
	
class Actividades_Tarea_Cli(BaseModel):		
	act_nombre : str
	act_cli_memo : str
	
class Actividades_Tarea(BaseModel):		
	act_nombre : str
	act_est_memo : str
	act_prof_memo : str
	act_cli_memo : str
	id_asg_act : str	

	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
	
class Actividades_Tarea_InDB(Actividades_Tarea):	
	id_actividad_tarea : str
	act_resultado : Union[str, None] = None # Aceptada, Atrazada, Rechazada, Iniciada 

class Actividades_Tarea_Eval(BaseModel):	
	act_resultado : str # Aceptada, Atrazada, Rechazada, Iniciada
	
class Actividades_Tarea_UPD(BaseModel):		
	act_nombre : str
	
class Actividades_Tarea_UPD_Est(BaseModel):
	act_est_memo : str
	
class Actividades_Tarea_UPD_Prf(BaseModel):	
	act_prof_memo : str
	
class Actividades_Tarea_UPD_Cli(BaseModel):	
	act_cli_memo : str		
	
#-------------------------
#-- ACTUALIZACIÓN TAREA --
#-------------------------
class Tareas_Actualizacion(BaseModel):	
	memo_actualizacion : str
	id_asg_upd : str	

	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	
	
class Tareas_Actualizacion_InDB(Tareas_Actualizacion):	
	id_tareas_act : str	
	fecha_actualizacion : date
	
class Tareas_Actualizacion_UPD(BaseModel):	
	memo_actualizacion : str
		
