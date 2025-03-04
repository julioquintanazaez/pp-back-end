from db.database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json
from uuid import UUID, uuid4  


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
	