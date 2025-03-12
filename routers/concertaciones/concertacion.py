from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Concertacion_Tema, User
from schemas.concertacion import Concertacion_Record, ConcertacionAdd, Concertacion_InDB, Concertacion_Eval, Concertacion_Activate, Concertacion_Actores
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from schemas.user import User_InDB
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

router = APIRouter()


@router.post("/crear_concertacion/", status_code=status.HTTP_201_CREATED)
async def crear_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					concertacion: ConcertacionAdd, db: Session = Depends(get_db)):
	try:
		db_concertacion = Concertacion_Tema(
			conc_tema = concertacion.conc_tema,
			conc_descripcion = concertacion.conc_descripcion,
			conc_valoracion_prof = concertacion.conc_valoracion_prof,
			conc_valoracion_cliente = concertacion.conc_valoracion_prof,
			conc_complejidad = concertacion.conc_complejidad,
			conc_actores_externos = concertacion.conc_actores_externos,
			conc_profesor_id = concertacion.conc_profesor_id,
			conc_cliente_id = concertacion.conc_cliente_id,
			conc_activa = False,
			conc_evaluacion = "Mejorable",
		)			
		db.add(db_concertacion)   	
		db.commit()
		db.refresh(db_concertacion)			
		return db_concertacion
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Concertación")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error SQLAlchemy creando el objeto Concertación")		


@router.get("/leer_concertacion/", status_code=status.HTTP_201_CREATED)  
async def leer_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	return db.query(Concertacion_Tema).offset(skip).limit(limit).all() 


@router.delete("/eliminar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_concertacion = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_concertacion is None:
		raise HTTPException(status_code=404, detail="La concertacion no existe en la base de datos")	
	db.delete(db_concertacion)	
	db.commit()
	return {"Result": "Concertacion eliminada satisfactoriamente"}


@router.put("/actualizar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_concertacion(current_user: Annotated[User_InDB, Security(get_current_active_user, scopes=["admin", "profesor, cliente"])], 
				id: str, concertacion: Concertacion_Record, db: Session = Depends(get_db)):
	
	db_conc = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_conc is None:
		raise HTTPException(status_code=404, detail="La concertacion de tema seleccionada no existen en la base de datos")
	db_conc.conc_tema = concertacion.conc_tema
	db_conc.conc_descripcion = concertacion.conc_descripcion
	db_conc.conc_valoracion_prof = concertacion.conc_valoracion_prof
	db_conc.conc_valoracion_cliente = concertacion.conc_valoracion_prof
	db_conc.conc_complejidad = concertacion.conc_complejidad
	db_conc.conc_actores_externos = concertacion.conc_actores_externos
	db.commit()
	db.refresh(db_conc)	
	return {"Result": "Datos de la concertacion de tema actualizados satisfactoriamente"}	
	

@router.put("/actualizar_responsables_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_responsables_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])], 
				id: str, concertacion: Concertacion_Actores, db: Session = Depends(get_db)):
	
	db_conc = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_conc is None:
		raise HTTPException(status_code=404, detail="La concertación de tema seleccionada no existen en la base de datos")
	db_conc.conc_profesor_id = concertacion.conc_profesor_id
	db_conc.conc_cliente_id = concertacion.conc_cliente_id	
	db.commit()
	db.refresh(db_conc)	
	return {"Result": "Datos de responsables de la concertación de tema actualizados satisfactoriamente"}	
	

@router.put("/evaluar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def evaluar_concertacion(current_user: Annotated[User_InDB, Security(get_current_active_user, scopes=["profesor"])], 
				id: str, conc_eva: Concertacion_Eval, db: Session = Depends(get_db)):
	
	db_concertacion = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_concertacion is None:
		raise HTTPException(status_code=404, detail="Concertación no existe ne base de datos")
	db_concertacion.conc_evaluacion = conc_eva.conc_evaluacion 	
	db.commit()
	db.refresh(db_concertacion)	
	return db_concertacion
	

@router.put("/activar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def activar_concertacion(current_user: Annotated[User_InDB, Security(get_current_active_user, scopes=["profesor"])], 
				id: str, concertacion: Concertacion_Activate, db: Session = Depends(get_db)):
	db_conc = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_conc is None:
		raise HTTPException(status_code=404, detail="La concertacion de tema seleccionada no existen en la base de datos")	
	db_conc.conc_activa = concertacion.conc_activa
	db.commit()
	db.refresh(db_conc)	
	return {"Result": "Cambio de concertacion desarrollada satisfactoriamente"}
