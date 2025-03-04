from db.database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json
from uuid import UUID, uuid4  

class Concertacion_Tema(Base):
	__tablename__ = "concertacion_tema"
	
	id_conc_tema = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)
	conc_tema = Column(String(50), unique=True, nullable=False, index=True)
	conc_descripcion = Column(String(200), nullable=False, index=True)
	conc_valoracion_prof = Column(String(200), nullable=False, index=True)
	conc_valoracion_cliente = Column(String(200), nullable=False, index=True)
	conc_complejidad = Column(String(15), nullable=False, index=True) #Alta, Baja, Media	
	conc_activa = Column(Boolean, nullable=False, index=True, default=True) 
	conc_evaluacion = Column(String(15), nullable=True, index=True) #Positiva, Mejorable
	conc_evaluacion_pred = Column(String(15), nullable=True, index=True) #Positiva, Mejorable
	conc_actores_externos = Column(Integer, nullable=False,  index=True) #N�mero de miembros en el equipo

	conc_profesor_id = Column(GUID, ForeignKey('profesor.id_profesor'), primary_key=True)   
	conc_cliente_id = Column(GUID, ForeignKey('cliente.id_cliente'), primary_key=True) 
