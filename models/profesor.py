from db.database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json
from uuid import UUID, uuid4  


class Profesor(Base):
	__tablename__ = "profesor"
	
	id_profesor = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	prf_genero = Column(String(5), nullable=False, index=True) 
	prf_estado_civil = Column(String(10), nullable=False, index=True)  #Soltero, Casado, Divorciado, Viudo
	prf_numero_empleos = Column(Integer, nullable=False, index=True) 
	prf_hijos = Column(Boolean, nullable=False, index=True) 
	prf_pos_tecnica_trabajo = Column(String(20), nullable=True, index=True) 
	prf_pos_tecnica_hogar = Column(String(20), nullable=True, index=True) 
	prf_trab_remoto = Column(Boolean, nullable=False, index=True) 
	prf_cargo = Column(Boolean, nullable=False, index=True) 
	prf_categoria_docente = Column(String(15), nullable=False, index=True) #Instructor, Auxiliar, Asistente, Titular
	prf_categoria_cientifica = Column(String(15), nullable=False, index=True) #Ingeniero, Licenciado, Master, Doctor, Tecnico
	prf_experiencia_practicas = Column(Boolean, nullable=False, index=True) 
	prf_numero_est_atendidos = Column(Integer, nullable=False, index=True) #Numero de estudiantes atendidos en el pasado

	prf_universidad_id = Column(GUID, ForeignKey("universidad.id_universidad"))
	prf_universidad = relationship("Universidad", back_populates="profesores")	
	profesor_concertacion = relationship("Cliente", secondary="concertacion_tema", back_populates="cliente_concertacion", cascade="all, delete") 	
	user_profesor_id = Column(GUID, ForeignKey("user.id"))
	user_profesor = relationship("User", back_populates="profesor")