from db.database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json
from uuid import UUID, uuid4  

class Universidad(Base):
	__tablename__ = "universidad"
	
	id_universidad = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE) 
	universidad_nombre = Column(String(50), unique=True, nullable=False, index=True) 
	universidad_siglas = Column(String(20), unique=True, nullable=True, index=True) 
	universidad_tec = Column(String(20), nullable=True, index=True) 
	universidad_transp = Column(Boolean, nullable=False, index=True) 
	universidad_teletrab = Column(Boolean, nullable=False, index=True) 
	
	estudiantes = relationship("Estudiante", back_populates="est_universidad", cascade="all, delete")
	profesores = relationship("Profesor", back_populates="prf_entidad_origen", cascade="all, delete")
