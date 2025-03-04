from db.database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json
from uuid import UUID, uuid4  

class Estudiante(Base): #Addicionar CI a todos los actores
	__tablename__ = "estudiante"
	
	id_estudiante = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	est_genero = Column(String(5), nullable=False, index=True) 
	est_estado_civil = Column(String(10), nullable=False, index=True)  #Soltero, Casado, Divorciado, Viudo
	est_trabajo = Column(Boolean, nullable=False, index=True) 
	est_becado = Column(Boolean, nullable=False, index=True) 
	est_hijos = Column(Boolean, nullable=False, index=True) 
	est_posibilidad_economica = Column(String(15), nullable=False, index=True) #Alta, Baja, Media
	est_pos_tecnica_escuela = Column(String(20), nullable=True, index=True) 
	est_pos_tecnica_hogar = Column(String(20), nullable=True, index=True) 
	est_trab_remoto = Column(Boolean, nullable=False, index=True) 

	user_estudiante_id = Column(GUID, ForeignKey("user.id"))
	user_estudiante = relationship("User", back_populates="estudiante")
	est_universidad_id = Column(GUID, ForeignKey("universidad.id_universidad"))
	est_universidad = relationship("Universidad", back_populates="estudiantes")
	tarea_estudiante_id = Column(GUID, ForeignKey("tarea.id_tarea"))
	tarea_estudiante = relationship("Tarea", back_populates="estudiante")
	