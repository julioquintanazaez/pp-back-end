from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Estudiante
from schemas.estudiante import Estudiante_Record, EstudianteAdd, Estudiante_InDB, Estudiante_Activo
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from schemas.user import User_InDB
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

router = APIRouter()

@router.post("/crear_estudiante/", status_code=status.HTTP_201_CREATED)
async def crear_estudiante(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					estudiante: EstudianteAdd, db: Session = Depends(get_db)):
	try:
		db_estudiante = Estudiante(
			est_trabajo = estudiante.est_trabajo, 
			est_becado = estudiante.est_becado, 
			est_posibilidad_economica = estudiante.est_posibilidad_economica, 
			est_pos_tecnica_escuela = estudiante.est_pos_tecnica_escuela,
			est_pos_tecnica_hogar = estudiante.est_pos_tecnica_hogar,
			est_trab_remoto = estudiante.est_trab_remoto,
			est_universidad_id = estudiante.est_universidad_id,	
			user_estudiante_id = estudiante.user_estudiante_id,
			tareas_estudiantes_id = estudiante.tareas_estudiantes_id
		)			
		db.add(db_estudiante)   	
		db.commit()
		db.refresh(db_estudiante)
		return db_estudiante
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Estudiante")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Estudiante")		


@router.get("/leer_estudiantes/", status_code=status.HTTP_201_CREATED)  
async def leer_estudiantes(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

		return db.query(Estudiante).offset(skip).limit(limit).all() 
		

@router.delete("/eliminar_estudiante/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_estudiante(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == id).first()
	if db_estudiante is None:
		raise HTTPException(status_code=404, detail="El estudiante no existe en la base de datos")	
	db.delete(db_estudiante)	
	db.commit()
	return {"Result": "Estudiante eliminado satisfactoriamente"}
	

@router.put("/actualizar_estudiante/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_estudiante(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])], 
				id: str, estudiante: Estudiante_Record, db: Session = Depends(get_db)):
	
	db_estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == id).first()
	if db_estudiante is None:
		raise HTTPException(status_code=404, detail="El estudiante seleccionado no existe en la base de datos")
	db_estudiante.est_trabajo = estudiante.est_trabajo
	db_estudiante.est_becado = estudiante.est_becado
	db_estudiante.est_posibilidad_economica = estudiante.est_posibilidad_economica
	db_estudiante.est_pos_tecnica_escuela = estudiante.est_pos_tecnica_escuela
	db_estudiante.est_pos_tecnica_hogar = estudiante.est_pos_tecnica_hogar
	db_estudiante.est_trab_remoto = estudiante.est_trab_remoto	
	db.commit()
	db.refresh(db_estudiante)	
	return {"Result": "Datos del estudiante actualizados satisfactoriamente"}

