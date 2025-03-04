from db.database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json
from uuid import UUID, uuid4  

class Cliente(Base):
	__tablename__ = "cliente"
	
	id_cliente = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	cli_genero = Column(String(5), nullable=False, index=True) 
	cli_estado_civil = Column(String(10), nullable=False, index=True)  #Soltero, Casado, Divorciado, Viudo
	cli_numero_empleos = Column(Integer, nullable=False, index=True) 
	cli_hijos = Column(Boolean, nullable=False, index=True) 
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
	user_cliente_id = Column(GUID, ForeignKey("user.id"))
	user_cliente = relationship("User", back_populates="cliente")
	cliente_concertacion = relationship("Profesor", secondary="concertacion_tema", back_populates="profesor_concertacion", cascade="all, delete") 	
