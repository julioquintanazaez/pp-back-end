from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Universidad
from schemas.universidad import UniversidadAdd, Universidad_InDB
from schemas.user import User_InDB
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

router = APIRouter()

@router.post("/crear_universidad/", status_code=status.HTTP_201_CREATED)
async def crear_universidad(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					universidad: UniversidadAdd, db: Session = Depends(get_db)):
	try:
		db_universidad = Universidad(
			universidad_nombre = universidad.universidad_nombre,
			universidad_siglas = universidad.universidad_siglas,
			universidad_tec = universidad.universidad_tec,
			universidad_transp = universidad.universidad_transp,
			universidad_teletrab = universidad.universidad_teletrab
		)			
		db.add(db_universidad)   	
		db.commit()
		db.refresh(db_universidad)			
		return db_universidad
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Universidad")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado SQLAlchemy creando el objeto Universidad")		


@router.get("/leer_universidades/", status_code=status.HTTP_201_CREATED)  
async def leer_universidades(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_universidades = db.query(Universidad).all()	
	return db_universidades
	

@router.delete("/eliminar_universidad/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_universidad(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_universidad = db.query(Universidad
						).filter(Universidad.id_universidad == id
						).first()
	if db_universidad is None:
		raise HTTPException(status_code=404, detail="La univeridad no existe en la base de datos")	
	db.delete(db_universidad)	
	db.commit()
	return {"Result": "Univeridad eliminada satisfactoriamente"}


@router.put("/actualizar_universidad/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_universidad(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])], 
				id: str, universidad_nueva: UniversidadAdd, db: Session = Depends(get_db)):
	db_universidad = db.query(Universidad).filter(Universidad.id_universidad == id).first()
	if db_universidad is None:
		raise HTTPException(status_code=404, detail="La universidad seleccionada no existe en la base de datos")
	db_universidad.universidad_nombre=universidad_nueva.universidad_nombre
	db_universidad.universidad_siglas=universidad_nueva.universidad_siglas
	db_universidad.universidad_tec=universidad_nueva.universidad_tec	
	db_universidad.universidad_transp=universidad_nueva.universidad_transp
	db_universidad.universidad_teletrab=universidad_nueva.universidad_teletrab
	db.commit()
	db.refresh(db_universidad)	
	return {"Result": "Universidad actualizada satisfactoriamente"}	
	
