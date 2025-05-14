#from db.database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json
from uuid import UUID, uuid4 
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class JSONEncodeDict(TypeDecorator):
	impl = String	
	cache_ok = True
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
	
	id = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)
	usuario = Column(String(30), unique=True, index=True) 
	email = Column(String(30), unique=True, nullable=False, index=True) 
	ci = Column(String(50), unique=True, nullable=False, index=True)
	nombre = Column(String(50), nullable=False, index=True) 
	primer_appellido = Column(String(50), nullable=False, index=True) 
	segundo_appellido = Column(String(50), nullable=False, index=True)  
	genero = Column(String(5), nullable=False, index=True) 
	estado_civil = Column(String(10), nullable=False, index=True)  
	hijos = Column(Boolean, nullable=False, index=True) 
	role = Column(JSONEncodeDict)
	deshabilitado = Column(Boolean, nullable=True, default=False)	
	hashed_password = Column(String(100), nullable=True, default=False)	
	
	profesor = relationship("Profesor", uselist=False, back_populates="user_profesor", cascade="all, delete")
	cliente = relationship("Cliente", uselist=False, back_populates="user_cliente", cascade="all, delete")
	estudiante = relationship("Estudiante", uselist=False, back_populates="user_estudiante", cascade="all, delete")

class Profesor(Base):
	__tablename__ = "profesor"
	
	id_profesor = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	prf_numero_empleos = Column(Integer, nullable=False, index=True) 
	prf_pos_tecnica_trabajo = Column(String(20), nullable=True, index=True) 
	prf_pos_tecnica_hogar = Column(String(20), nullable=True, index=True) 
	prf_trab_remoto = Column(Boolean, nullable=False, index=True) 
	prf_cargo = Column(Boolean, nullable=False, index=True) 
	prf_categoria_docente = Column(String(15), nullable=False, index=True) 
	prf_categoria_cientifica = Column(String(15), nullable=False, index=True) 
	prf_experiencia_practicas = Column(Boolean, nullable=False, index=True) 
	prf_numero_est_atendidos = Column(Integer, nullable=False, index=True) 

	prf_universidad_id = Column(GUID, ForeignKey("universidad.id_universidad"))
	prf_universidad = relationship("Universidad", back_populates="profesores")	
	user_profesor_id = Column(GUID, ForeignKey("user.id"), unique=True)
	user_profesor = relationship("User", back_populates="profesor")
	
	profesor_concertacion = relationship("Cliente", secondary="concertacion_tema", back_populates="cliente_concertacion", cascade="all, delete") 	

class Centro_Practicas(Base):
	__tablename__ = "centro_practicas"
	
	id_centro = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	centro_nombre = Column(String(50), unique=True, nullable=False, index=True) 
	centro_siglas = Column(String(20), unique=True, nullable=True, index=True)
	centro_tec = Column(String(20), nullable=True, index=True) 
	centro_transp = Column(Boolean, nullable=False, index=True) 
	centro_experiencia = Column(Boolean, nullable=False, index=True) 
	centro_teletrab = Column(Boolean, nullable=False, index=True) 
	
	clientes = relationship("Cliente", back_populates="cli_centro_practicas", cascade="all, delete")

class Universidad(Base):
	__tablename__ = "universidad"
	
	id_universidad = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	universidad_nombre = Column(String(50), unique=True, nullable=False, index=True) 
	universidad_siglas = Column(String(20), unique=True, nullable=True, index=True) 
	universidad_tec = Column(String(20), nullable=True, index=True) 
	universidad_transp = Column(Boolean, nullable=False, index=True) 
	universidad_teletrab = Column(Boolean, nullable=False, index=True) 
	
	estudiantes = relationship("Estudiante", back_populates="est_universidad", cascade="all, delete")
	profesores = relationship("Profesor", back_populates="prf_universidad", cascade="all, delete")

class Cliente(Base):
	__tablename__ = "cliente"
	
	id_cliente = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	cli_numero_empleos = Column(Integer, nullable=False, index=True) 
	cli_pos_tecnica_trabajo = Column(String(20), nullable=True, index=True) 
	cli_pos_tecnica_hogar = Column(String(20), nullable=True, index=True) 
	cli_cargo = Column(Boolean, nullable=False, index=True) 
	cli_trab_remoto = Column(Boolean, nullable=False, index=True) 
	cli_categoria_docente = Column(String(5), nullable=False, index=True) #Instructor, Auxiliar, Asistente, Titular, Ninguna
	cli_categoria_cientifica = Column(String(5), nullable=False, index=True) #Ingeniero, Licenciado, Master, Doctor, Tecnico, Ninguna
	cli_experiencia_practicas = Column(Boolean, nullable=False, index=True) 
	cli_numero_est_atendidos = Column(Integer, nullable=False, index=True) #Numero de estudiantes atendidos en el pasado

	cli_centro_id = Column(GUID, ForeignKey("centro_practicas.id_centro"))
	cli_centro_practicas = relationship("Centro_Practicas", back_populates="clientes")
	user_cliente_id = Column(GUID, ForeignKey("user.id"), unique=True)
	user_cliente = relationship("User", back_populates="cliente")
	
	cliente_concertacion = relationship("Profesor", secondary="concertacion_tema", back_populates="profesor_concertacion", cascade="all, delete") 	

class Concertacion_Tema(Base):
	__tablename__ = "concertacion_tema"
	
	id_conc_tema = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)
	conc_tema = Column(String(50), unique=True, nullable=False, index=True)
	conc_descripcion = Column(String(200), nullable=False, index=True)
	conc_valoracion_prof = Column(String(200), nullable=False, index=True)
	conc_valoracion_cliente = Column(String(200), nullable=False, index=True)
	conc_complejidad = Column(String(15), nullable=False, index=True) #Alta, Baja, Media	
	conc_activa = Column(Boolean, nullable=True, index=True, default=True) 
	conc_evaluacion = Column(String(15), nullable=True, index=True, default="Mejorable") #Positiva, Mejorable
	conc_evaluacion_pred = Column(String(15), nullable=True, index=True) #Positiva, Mejorable
	conc_actores_externos = Column(Integer, nullable=False,  index=True) #N�mero de miembros en el equipo

	conc_profesor_id = Column(GUID, ForeignKey('profesor.id_profesor'), primary_key=True)   
	conc_cliente_id = Column(GUID, ForeignKey('cliente.id_cliente'), primary_key=True) 
	tareas = relationship("Tarea", back_populates="concertacion_tareas", cascade="all, delete")

class Tarea(Base):
	__tablename__ = "tarea"
	
	id_tarea = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	tarea_tipo = Column(String(20), unique=False, nullable=False, index=True) 
	tarea_descripcion = Column(String(200), unique=False, nullable=False, index=True) 
	tarea_fecha_inicio = Column(DateTime, nullable=False)
	tarea_fecha_fin = Column(DateTime, nullable=False)
	tarea_complejidad_estimada = Column(String(50), nullable=False, index=True) 
	tarea_participantes = Column(Integer, nullable=False,  index=True) #N�mero de miembros en el equipo
	tarea_asignada = Column(Boolean, nullable=True, index=True, default=True) 
	tarea_activa = Column(Boolean, nullable=False, index=True, default=True) 
	tarea_evaluacion = Column(String(15), nullable=True, index=True, default="Mejorable") #Positiva, Mejorable
	tarea_evaluacion_pred = Column(String(15), nullable=True, index=True) #Positiva, Mejorable 

	concertacion_tarea_id = Column(GUID, ForeignKey("concertacion_tema.id_conc_tema"))
	concertacion_tareas = relationship("Concertacion_Tema", back_populates="tareas")	
	estudiantes = relationship("Estudiante", back_populates="tareas_estudiantes", cascade="all, delete")
		
class Estudiante(Base): #Addicionar CI a todos los actores
	__tablename__ = "estudiante"
	
	id_estudiante = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	est_trabajo = Column(Boolean, nullable=False, index=True) 
	est_becado = Column(Boolean, nullable=False, index=True) 
	est_posibilidad_economica = Column(String(15), nullable=False, index=True) #Alta, Baja, Media
	est_pos_tecnica_escuela = Column(String(20), nullable=True, index=True) 
	est_pos_tecnica_hogar = Column(String(20), nullable=True, index=True) 
	est_trab_remoto = Column(Boolean, nullable=False, index=True) 
	est_ocupado = Column(Boolean, nullable=True, index=True, default=False) 

	user_estudiante_id = Column(GUID, ForeignKey("user.id"), unique=True)
	user_estudiante = relationship("User", back_populates="estudiante")
	est_universidad_id = Column(GUID, ForeignKey("universidad.id_universidad"))
	est_universidad = relationship("Universidad", back_populates="estudiantes")
	tareas_estudiantes_id = Column(GUID, ForeignKey("tarea.id_tarea"))
	tareas_estudiantes = relationship("Tarea", back_populates="estudiantes")	
