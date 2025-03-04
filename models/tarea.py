from db.database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json
from uuid import UUID, uuid4  

class Tarea(Base):
	__tablename__ = "tarea"
	
	id_tarea = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	tarea_descripcion = Column(String(200), unique=True, nullable=False, index=True) 
	tarea_fecha_inicio = Column(DateTime, nullable=False)
	tarea_fecha_fin = Column(DateTime, nullable=False)
	tarea_complejidad_estimada = Column(String(50), nullable=False, index=True) 
	tarea_participantes = Column(Integer, nullable=False,  index=True) #N�mero de miembros en el equipo
	tarea_asignada = Column(Boolean, nullable=True, index=True, default=True) 
	tarea_activa = Column(Boolean, nullable=False, index=True, default=True) 
	tarea_evaluacion = Column(String(15), nullable=True, index=True) #Positiva, Mejorable
	tarea_evaluacion_pred = Column(String(15), nullable=True, index=True) #Positiva, Mejorable 

	asg_conc_id = Column(GUID, ForeignKey('concertacion_tema.id_conc_tema'), primary_key=True) 	
	estudiante = relationship("Estudiante", uselist=False, back_populates="tarea_estudiante", cascade="all, delete")
		