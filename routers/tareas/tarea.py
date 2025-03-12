from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Tarea
from schemas.tarea import Tarea_Record, TareaAdd, Tarea_InDB, Tarea_Eval
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from schemas.user import User_InDB
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

router = APIRouter()

@router.post("/crear_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_tarea(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					asg_tarea: TareaAdd, db: Session = Depends(get_db)):
	try:
		db_tarea = Tarea(
			tarea_descripcion = asg_tarea.asg_descripcion,
			tarea_fecha_inicio = asg_tarea.asg_fecha_inicio, 
			tarea_fecha_fin = asg_tarea.asg_fecha_fin, 
			tarea_complejidad_estimada = asg_tarea.asg_complejidad_estimada, 
			tarea_participantes = asg_tarea.asg_participantes,  #Numero de miembros en el equipo
			tarea_tipo = asg_tarea.asg_tipo_tarea_id,
			tarea_conc_id = asg_tarea.asg_conc_id,
			tarea_evaluacion = "Mejorable"
		)			
		db.add(db_tarea)   	
		db.commit()
		db.refresh(db_tarea)			
		return db_tarea
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Tarea")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error SQLAlchemy creando el objeto Tarea")		


@router.get("/leer_tareas/", status_code=status.HTTP_201_CREATED)  
async def leer_tareas(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

		return db.query(Tarea).offset(skip).limit(limit).all() 
		

@router.delete("/eliminar_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_tarea(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_tarea = db.query(Tarea).filter(Tarea.id_asignacion == id).first()
	if db_tarea is None:
		raise HTTPException(status_code=404, detail="La tarea no existe en la base de datos")	
	db.delete(db_tarea)	
	db.commit()
	return {"Result": "Tarea eliminada satisfactoriamente"}


@router.put("/actualizar_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_tarea(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, tarea: Tarea_Record, db: Session = Depends(get_db)):
	
	db_tarea = db.query(Tarea).filter(Tarea.id_asignacion == id).first()
	if db_tarea is None:
		raise HTTPException(status_code=404, detail="La asignacion de tareas seleccionada no existen en la base de datos")
	db_tarea.tarea_descripcion = tarea.tarea_descripcion
	db_tarea.tarea_fecha_inicio = tarea.tarea_fecha_inicio
	db_tarea.tarea_fecha_fin = tarea.tarea_fecha_fin
	db_tarea.tarea_complejidad_estimada = tarea.tarea_complejidad_estimada
	db_tarea.tarea_participantes = tarea.tarea_participantes
	db_tarea.tarea_tipo = tarea.tarea_tipo
	db.commit()
	db.refresh(db_tarea)	
	return {"Result": "Datos de la asignacion actualizados satisfactoriamente"}	
	

@router.put("/evaluar_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def evaluar_tarea(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor"])], 
				id: str, tarea_eva: Tarea_Eval, db: Session = Depends(get_db)):
	db_tarea = db.query(Tarea).filter(Tarea.id_tarea == id).first()
	if db_tarea is None:
		raise HTTPException(status_code=404, detail="Tarea no existe ne la base de datos")
	db_tarea.tarea_evaluacion = tarea_eva.tarea_evaluacion 	
	db.commit()
	db.refresh(db_tarea)	
	return db_tarea
	

