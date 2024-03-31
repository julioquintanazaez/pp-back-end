from database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json

from uuid import UUID, uuid4  

class JSONEncodeDict(TypeDecorator):
	impl = String
	
	def process_bind_param(self, value, dialect):
		if value is not None:
			value = json.dumps(value)
		return value

	def process_result_value(self, value, dialect):
		if value is not None:
			value = json.loads(value)
		return value
		
class User(Base):
	__tablename__ = "user"
	
	username = Column(String(30), primary_key=True, unique=True, index=True) 
	full_name = Column(String(50), nullable=True, index=True) 
	email = Column(String(30), unique=True, nullable=False, index=True) 
	#role = Column(String(15), nullable=False, index=True)#List[] #Scopes
	role = Column(JSONEncodeDict)
	disable = Column(Boolean, nullable=True, default=False)	
	hashed_password = Column(String(100), nullable=True, default=False)	

class Entidad_Origen(Base):
	__tablename__ = "entidad_origen"
	
	id_entidad_origen = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	org_nombre = Column(String(50), unique=True, nullable=False, index=True) 
	org_siglas = Column(String(20), unique=True, nullable=True, index=True) 
	org_nivel_tecnologico = Column(JSONEncodeDict)
	org_transporte = Column(Boolean, nullable=False, index=True) 
	org_trab_remoto = Column(Boolean, nullable=False, index=True) 
	#Relacion 1-M con tabla hija "Estudiante"
	estudiantes = relationship("Estudiante", back_populates="est_entidad_origen")
	#Relacion 1-M con tabla hija "Profesor"
	profesores = relationship("Profesor", back_populates="prf_entidad_origen")

class Entidad_Destino(Base):
	__tablename__ = "entidad_destino"
	
	id_entidad_destino = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	dest_nombre = Column(String(50), unique=True, nullable=False, index=True) 
	dest_siglas = Column(String(20), unique=True, nullable=True, index=True)
	dest_nivel_tecnologico = Column(JSONEncodeDict)
	dest_transporte = Column(Boolean, nullable=False, index=True) 
	dest_experiencia = Column(Boolean, nullable=False, index=True) 
	dest_trab_remoto = Column(Boolean, nullable=False, index=True) 
	#Relacion 1-M con tabla hija "Cliente"
	clientes = relationship("Cliente", back_populates="cli_entidad_destino")
	
class Profesor(Base):
	__tablename__ = "profesor"
	
	id_profesor = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	prf_ci = Column(String(50), unique=True, nullable=False, index=True)
	prf_nombre = Column(String(50), nullable=False, index=True) 
	prf_primer_appellido = Column(String(50), nullable=False, index=True) 
	prf_segundo_appellido = Column(String(50), nullable=False, index=True) 
	prf_correo = Column(String(30), unique=True, nullable=False, index=True) 
	prf_genero = Column(String(5), nullable=False, index=True) 
	prf_estado_civil = Column(String(10), nullable=False, index=True)  #Soltero, Casado, Divorciado, Viudo
	prf_numero_empleos = Column(Integer, nullable=False, index=True) 
	prf_hijos = Column(Boolean, nullable=False, index=True) 
	prf_pos_tecnica_trabajo = Column(JSONEncodeDict)
	prf_pos_tecnica_hogar = Column(JSONEncodeDict)
	prf_trab_remoto = Column(Boolean, nullable=False, index=True) 
	prf_cargo = Column(Boolean, nullable=False, index=True) 
	prf_categoria_docente = Column(String(5), nullable=False, index=True) #Instructor, Auxiliar, Asistente, Titular
	prf_categoria_cientifica = Column(String(5), nullable=False, index=True) #Ingeniero, Licenciado, Master, Doctor, Tecnico
	prf_experiencia_practicas = Column(Boolean, nullable=False, index=True) 
	prf_numero_est_atendidos = Column(Integer, nullable=False, index=True) #Numero de estudiantes atendidos en el pasado
	#Relacion M-1 con tabla padre "Entidad_Origen"
	prf_entidad_id = Column(GUID, ForeignKey("entidad_origen.id_entidad_origen"))
	prf_entidad_origen = relationship("Entidad_Origen", back_populates="profesores")	
	#Relacion Many-to-Many con tabla "Cliente" y asiciacion con tabla "Asignacion_Tareas"
	profesor_concertacion = relationship("Cliente", secondary="concertacion_tema", back_populates="cliente_concertacion") 	
	
class Cliente(Base):
	__tablename__ = "cliente"
	
	id_cliente = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	cli_ci = Column(String(50), unique=True, nullable=False, index=True)
	cli_nombre = Column(String(50), nullable=False, index=True) 
	cli_primer_appellido = Column(String(50), nullable=False, index=True) 
	cli_segundo_appellido = Column(String(50), nullable=False, index=True) 
	cli_correo = Column(String(30), unique=True, nullable=False, index=True) 
	cli_genero = Column(String(5), nullable=False, index=True) 
	cli_estado_civil = Column(String(10), nullable=False, index=True)  #Soltero, Casado, Divorciado, Viudo
	cli_numero_empleos = Column(Integer, nullable=False, index=True) 
	cli_hijos = Column(Boolean, nullable=False, index=True) 
	cli_pos_tecnica_trabajo = Column(JSONEncodeDict)
	cli_pos_tecnica_hogar = Column(JSONEncodeDict)
	cli_cargo = Column(Boolean, nullable=False, index=True) 
	cli_trab_remoto = Column(Boolean, nullable=False, index=True) 
	cli_categoria_docente = Column(String(5), nullable=False, index=True) #Instructor, Auxiliar, Asistente, Titular, Ninguna
	cli_categoria_cientifica = Column(String(5), nullable=False, index=True) #Ingeniero, Licenciado, Master, Doctor, Tecnico, Ninguna
	cli_experiencia_practicas = Column(Boolean, nullable=False, index=True) 
	cli_numero_est_atendidos = Column(Integer, nullable=False, index=True) #Numero de estudiantes atendidos en el pasado
	#Relacion M-1 con tabla padre "Entidad_Destino"
	cli_entidad_id = Column(GUID, ForeignKey("entidad_destino.id_entidad_destino"))
	cli_entidad_destino = relationship("Entidad_Destino", back_populates="clientes")
	#Relacion Many-to-Many con tabla "Profesor" y asiciacion con tabla "Concertacion tema"
	cliente_concertacion = relationship("Profesor", secondary="concertacion_tema", back_populates="profesor_concertacion") 	

class Concertacion_Tema(Base):
	__tablename__ = "concertacion_tema"
	
	id_conc_tema = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)
	conc_tema = Column(String(50), unique=True, nullable=False, index=True)
	conc_descripcion = Column(String(200), nullable=False, index=True)
	conc_valoracion_prof = Column(String(200), nullable=False, index=True)
	conc_valoracion_cliente = Column(String(200), nullable=False, index=True)
	conc_complejidad = Column(String(15), nullable=False, index=True) #Alta, Baja, Media	
	conc_activa = Column(Boolean, nullable=False, index=True, default=True) 
	conc_evaluacion = Column(String(15), nullable=True, index=True) #Positiva, Ngativa, Mejorable
	conc_evaluacion_pred = Column(String(15), nullable=True, index=True) #Positiva, Ngativa, Mejorable
	conc_actores_externos = Column(Integer, nullable=False,  index=True) #Número de miembros en el equipo
	#Id de asociacion
	conc_profesor_id = Column(GUID, ForeignKey('profesor.id_profesor'), primary_key=True)   
	conc_cliente_id = Column(GUID, ForeignKey('cliente.id_cliente'), primary_key=True) 
	#Relacion Many-to-Many con Estudiantes y se refleja en tabla Asignacion_Tareas
	conce_est_tarea = relationship("Estudiante", secondary="asignacion_tarea", back_populates="est_conc_tarea") 	
	
class Estudiante(Base): #Addicionar CI a todos los actores
	__tablename__ = "estudiante"
	
	id_estudiante = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	est_ci = Column(String(50), unique=True, nullable=False, index=True)
	est_nombre = Column(String(50), nullable=False, index=True) 
	est_primer_appellido = Column(String(50), nullable=False, index=True) 
	est_segundo_appellido = Column(String(50), nullable=False, index=True) 
	est_correo = Column(String(30), unique=True, nullable=False, index=True) 
	est_genero = Column(String(5), nullable=False, index=True) 
	est_estado_civil = Column(String(10), nullable=False, index=True)  #Soltero, Casado, Divorciado, Viudo
	est_trabajo = Column(Boolean, nullable=False, index=True) 
	est_becado = Column(Boolean, nullable=False, index=True) 
	est_hijos = Column(Boolean, nullable=False, index=True) 
	est_posibilidad_economica = Column(String(15), nullable=False, index=True) #Alta, Baja, Media
	est_pos_tecnica_escuela = Column(JSONEncodeDict)
	est_pos_tecnica_hogar = Column(JSONEncodeDict)
	est_trab_remoto = Column(Boolean, nullable=False, index=True) 
	#Relacion M-1 con tabla padre "Entidad_Origen"
	est_entidad_id = Column(GUID, ForeignKey("entidad_origen.id_entidad_origen"))
	est_entidad_origen = relationship("Entidad_Origen", back_populates="estudiantes")	
	#Relacion Many-to-Many con tabla "Concertacion_Tema" se refleja en tabla Asignacion_Tareas
	est_conc_tarea = relationship("Concertacion_Tema", secondary="asignacion_tarea", back_populates="conce_est_tarea") 	

class Tipo_Tarea(Base):
	__tablename__ = "tipo_tarea"
	
	id_tipo_tarea = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	tarea_tipo_nombre = Column(String(50), unique=True, nullable=False, index=True) 
	#Relacion con table padre
	tarea_asignacion = relationship("Asignacion_Tarea", back_populates="tarea_tipo")
	
class Asignacion_Tarea(Base):
	__tablename__ = "asignacion_tarea"
	
	id_asignacion = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	asg_descripcion = Column(String(200), unique=True, nullable=False, index=True) 
	asg_fecha_inicio = Column(DateTime, nullable=False)
	asg_fecha_fin = Column(DateTime, nullable=False)
	asg_complejidad_estimada = Column(String(50), nullable=False, index=True) 
	asg_participantes = Column(Integer, nullable=False,  index=True) #Número de miembros en el equipo
	asg_evaluacion = Column(Float, nullable=True,  index=True) # con average de actividades
	asg_asignada = Column(Boolean, nullable=True, index=True, default=True) 
	asg_activa = Column(Boolean, nullable=False, index=True, default=True) 
	asg_evaluacion = Column(String(15), nullable=True, index=True) #Positiva, Ngativa, Mejorable
	asg_evaluacion_pred = Column(String(15), nullable=True, index=True) #Positiva, Ngativa, Mejorable
	#Relacion M-1 con tabla Padre "Tipo_Tarea"
	asg_tipo_tarea_id = Column(GUID, ForeignKey("tipo_tarea.id_tipo_tarea"))
	tarea_tipo = relationship("Tipo_Tarea", back_populates="tarea_asignacion")
	#Relacion 1-M con tabla hija "Actividades_Tarea"
	asg_actividades = relationship("Actividades_Tarea", back_populates="act_tarea")
	#Relacion 1-M con tabla hija "Tareas_Actualizacion"
	asg_actualizacion = relationship("Tareas_Actualizacion", back_populates="actualizacion_tarea")
	#Id de la relacion entre Estudiante y Concertacion_Tema
	asg_estudiante_id = Column(GUID, ForeignKey('estudiante.id_estudiante'), primary_key=True) 
	asg_conc_id = Column(GUID, ForeignKey('concertacion_tema.id_conc_tema'), primary_key=True) 	
		
class Actividades_Tarea(Base):
	__tablename__ = "actividades_tarea"
	
	id_actividad_tarea = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	act_nombre = Column(String(100), nullable=False, index=True) 
	act_resultado = Column(String(15), nullable=True,  index=True) # Aceptada, Atrazada, Rechazada
	act_est_memo = Column(String(200), nullable=True,  index=True)
	act_prof_memo = Column(String(200), nullable=True,  index=True)
	act_cli_memo = Column(String(200), nullable=True,  index=True)
	#Relacion M-1 con tabla padre "Asignacion_Tareas"
	id_asg_act = Column(GUID, ForeignKey("asignacion_tarea.id_asignacion"))
	act_tarea = relationship("Asignacion_Tarea", back_populates="asg_actividades")
	
class Tareas_Actualizacion(Base):
	__tablename__ = "tareas_actualizacion"
	
	id_tareas_act = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 	
	fecha_actualizacion = Column(DateTime, nullable=False)
	memo_actualizacion = Column(String(200), nullable=True,  index=True)
	#Relacion M-1 con tabla padre "Asignacion Tarea"
	id_asg_upd = Column(GUID, ForeignKey("asignacion_tarea.id_asignacion"))
	actualizacion_tarea = relationship("Asignacion_Tarea", back_populates="asg_actualizacion")
	
	
