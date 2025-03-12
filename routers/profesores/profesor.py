from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Profesor
from schemas.profesor import Profesor_Record, ProfesorAdd, Profesor_InDB
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from schemas.user import User_InDB
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

router = APIRouter()

@router.post("/crear_profesor/", status_code=status.HTTP_201_CREATED)
async def crear_profesor(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					profesor: ProfesorAdd, db: Session = Depends(get_db)):
	try:
		db_profesor = Profesor(
			prf_numero_empleos = profesor.prf_numero_empleos,
			prf_pos_tecnica_trabajo = profesor.prf_pos_tecnica_trabajo,
			prf_pos_tecnica_hogar = profesor.prf_pos_tecnica_hogar,
			prf_cargo = profesor.prf_cargo,
			prf_trab_remoto = profesor.prf_trab_remoto,
			prf_categoria_docente = profesor.prf_categoria_docente, #Instructor, Auxiliar, Asistente, Titular
			prf_categoria_cientifica = profesor.prf_categoria_cientifica,  #Ingeniero, Licenciado, Master, Doctor, Tecnico
			prf_experiencia_practicas = profesor.prf_experiencia_practicas, 
			prf_numero_est_atendidos = profesor.prf_numero_est_atendidos,  #Numero de estudiantes atendidos en el pasado
			prf_entidad_id = profesor.prf_entidad_id,	
			user_profesor_id = profesor.user_profesor_id	
		)			
		db.add(db_profesor)   	
		db.commit()
		return db_profesor		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Profesor")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error SQLAlchemy creando el objeto Profesor")		

@router.get("/leer_profesores/", status_code=status.HTTP_201_CREATED)  
async def leer_profesores(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	return db.query(Profesor).offset(skip).limit(limit).all() 
	

@router.delete("/eliminar_profesor/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_profesor(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
    db_profesor = db.query(Profesor).filter(Profesor.id_profesor == id).first()
    if db_profesor is None:
        raise HTTPException(status_code=404, detail="El profesor no existe en la base de datos")		
    return {"Result": "Profesor eliminado satisfactoriamente"}

@router.put("/actualizar_profesor/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_profesor(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor"])], 
				id: str, profesor: Profesor_Record, db: Session = Depends(get_db)):
				
	db_profesor = db.query(Profesor).filter(Profesor.id_profesor == id).first()
	if db_profesor is None:
		raise HTTPException(status_code=404, detail="El profesor seleccionado no existe en la base de datos")
	db_profesor.prf_numero_empleos = profesor.prf_numero_empleos
	db_profesor.prf_pos_tecnica_trabajo = profesor.prf_pos_tecnica_trabajo
	db_profesor.prf_pos_tecnica_hogar = profesor.prf_pos_tecnica_hogar
	db_profesor.prf_cargo = profesor.prf_cargo
	db_profesor.prf_trab_remoto = profesor.prf_trab_remoto
	db_profesor.prf_categoria_docente = profesor.prf_categoria_docente
	db_profesor.prf_categoria_cientifica = profesor.prf_categoria_cientifica
	db_profesor.prf_experiencia_practicas = profesor.prf_experiencia_practicas 
	db_profesor.prf_numero_est_atendidos = profesor.prf_numero_est_atendidos
	db.commit()
	db.refresh(db_profesor)	
	return {"Result": "Datos del profesor actualizados satisfactoriamente"}	

