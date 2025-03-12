from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Centro_Practicas
from schemas.centro_practicas import Centro_PracticasAdd, Centro_Practicas_InDB
from schemas.user import User_InDB
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

router = APIRouter()

@router.post("/crear_centropracticas/", status_code=status.HTTP_201_CREATED)
async def crear_centropracticas(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					practicas: Centro_PracticasAdd, db: Session = Depends(get_db)):
	try:
		db_practicas = Centro_Practicas(
			centro_nombre = practicas.dest_nombre,
			centro_siglas = practicas.dest_siglas,
			centro_tec = practicas.dest_nivel_tecnologico,
			centro_transp = practicas.dest_transporte,
			centro_experiencia = practicas.dest_experiencia,
			centro_teletrab = practicas.dest_trab_remoto
		)			
		db.add(db_practicas)   	
		db.commit()
		db.refresh(db_practicas)			
		return db_practicas
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Centro Prácticas")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Centro Prácticas")		


@router.get("/leer_centropracticas/", status_code=status.HTTP_201_CREATED)  
async def leer_centropracticas(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_practicas = db.query(Centro_Practicas).all()	
	return db_practicas


@router.delete("/eliminar_centropracticas/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_centropracticas(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_practicas = db.query(Centro_Practicas
						).filter(Centro_Practicas.id_centro == id
						).first()
	if db_practicas is None:
		raise HTTPException(status_code=404, detail="La Entidad Destino no existe en la base de datos")	
	db.delete(db_practicas)	
	db.commit()
	return {"Result": "Centro prácticas eliminada satisfactoriamente"}

		
@router.put("/actualizar_centropracticas/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_centropracticas(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])], 
				id: str, centro_nuevo: Centro_PracticasAdd, db: Session = Depends(get_db)):
	
	db_practicas = db.query(Centro_Practicas).filter(Centro_Practicas.id_centro == id).first()
	if db_practicas is None:
		raise HTTPException(status_code=404, detail="La entidad seleccionada no existen en la base de datos")
	db_practicas.centro_nombre=centro_nuevo.centro_nombre
	db_practicas.centro_siglas=centro_nuevo.centro_siglas
	db_practicas.centro_tec=centro_nuevo.centro_tec	
	db_practicas.centro_transp=centro_nuevo.centro_transp
	db_practicas.centro_teletrab=centro_nuevo.centro_teletrab
	db_practicas.centro_experiencia=centro_nuevo.centro_experiencia
	db.commit()
	db.refresh(db_practicas)	
	return {"Result": "Entidad Destino actualizada satisfactoriamente"}
	
