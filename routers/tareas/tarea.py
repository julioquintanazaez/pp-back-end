from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Tarea, Profesor, Concertacion_Tema, Cliente, Estudiante, User
from schemas.tarea import Tarea_Record, TareaAdd, Tarea_InDB, Tarea_Eval
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from schemas.user import User_InDB
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
import pandas as pd
import joblib
from core import config

router = APIRouter()

@router.post("/crear_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_tarea(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					tarea: TareaAdd, db: Session = Depends(get_db)):
	try:
		db_tarea = Tarea(
			tarea_descripcion = tarea.tarea_descripcion,
			tarea_fecha_inicio = tarea.tarea_fecha_inicio, 
			tarea_fecha_fin = tarea.tarea_fecha_fin, 
			tarea_complejidad_estimada = tarea.tarea_complejidad_estimada, 
			tarea_participantes = tarea.tarea_participantes,  
			tarea_tipo = tarea.tarea_tipo,
			concertacion_tarea_id = tarea.concertacion_tarea_id,
		)			
		db.add(db_tarea)   	
		db.commit()
		db.refresh(db_tarea)			
		return db_tarea
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Tarea")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error SQLAlchemy creando el objeto Tarea")		


@router.delete("/eliminar_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_tarea(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_tarea = db.query(Tarea).filter(Tarea.id_tarea == id).first()
	if db_tarea is None:
		raise HTTPException(status_code=404, detail="La tarea no existe en la base de datos")	
	db.delete(db_tarea)	
	db.commit()
	return {"Result": "Tarea eliminada satisfactoriamente"}


@router.put("/actualizar_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_tarea(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor"])], 
				id: str, tarea: Tarea_Record, db: Session = Depends(get_db)):
	
	db_tarea = db.query(Tarea).filter(Tarea.id_tarea == id).first()
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

@router.get("/leer_tarea_estudiante/", status_code=status.HTTP_201_CREATED)  
async def leer_tarea_estudiante(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	db_estudiante = db.query(Estudiante).filter(Estudiante.user_estudiante_id == current_user.id).first()
	db_tarea = db.query(Tarea).filter(
		Tarea.id_tarea == db_estudiante.tareas_estudiantes_id).first()
	db_concertacion = db.query(Concertacion_Tema).filter(
		Concertacion_Tema.id_conc_tema == db_tarea.concertacion_tarea_id).first()
	return {"concertacion": db_concertacion, 
		 	"tarea": db_tarea, 
			"estudiante": db_estudiante, 
		 }

@router.get("/leer_tareas_cliente/", status_code=status.HTTP_201_CREATED)  
async def leer_tareas_cliente(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["cliente"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

	#Datos Profesor
	est_query = db.query(
		User.id.label('est_user_id'),
		User.nombre.label('est_nombre'),
		User.primer_appellido.label('est_primer_appellido'),
		User.segundo_appellido.label('est_segundo_appellido'),
	).select_from(
		User
	).subquery()

	#Datos Profesor
	prf_query = db.query(
		User.id.label('prf_user_id'),
		User.nombre.label('prf_nombre'),
		User.primer_appellido.label('prf_primer_appellido'),
		User.segundo_appellido.label('prf_segundo_appellido'),
	).select_from(
		User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		User.id.label('cli_user_id'),
		User.nombre.label('cli_nombre'),
		User.primer_appellido.label('cli_primer_appellido'),
		User.segundo_appellido.label('cli_segundo_appellido'),
	).select_from(
		User
	).subquery()	

	db_tarea = db.query(
			#Datos de Concertacion
			Concertacion_Tema.id_conc_tema,
			Concertacion_Tema.conc_tema,
			Concertacion_Tema.conc_cliente_id,
			Concertacion_Tema.conc_profesor_id,
			#Datos de profesor
			Profesor.id_profesor,			
			prf_query.c.prf_user_id,
			prf_query.c.prf_nombre,
			prf_query.c.prf_primer_appellido,
			prf_query.c.prf_segundo_appellido,
			#Datos de cliente
			Cliente.id_cliente,
			cli_query.c.cli_user_id,
			cli_query.c.cli_nombre,
			cli_query.c.cli_primer_appellido,
			cli_query.c.cli_segundo_appellido,
			#Datos de estudiante
			Estudiante.id_estudiante,
			est_query.c.est_user_id,
			est_query.c.est_nombre,
			est_query.c.est_primer_appellido,
			est_query.c.est_segundo_appellido,
			#Datos de tareas
			Tarea.id_tarea,
			Tarea.concertacion_tarea_id,
			Tarea.tarea_activa,
			Tarea.tarea_asignada,
			Tarea.tarea_complejidad_estimada,
			Tarea.tarea_descripcion,
			Tarea.tarea_evaluacion,
			Tarea.tarea_evaluacion_pred,
			Tarea.tarea_fecha_fin,
			Tarea.tarea_fecha_inicio,
			Tarea.tarea_participantes,
			Tarea.tarea_tipo
			).select_from(Tarea
			).join(Concertacion_Tema, Concertacion_Tema.id_conc_tema == Tarea.concertacion_tarea_id
		  	).join(Estudiante, Estudiante.tareas_estudiantes_id == Tarea.id_tarea
			).join(est_query, est_query.c.est_user_id == Estudiante.user_estudiante_id	
			).join(Profesor, Profesor.id_profesor == Concertacion_Tema.conc_profesor_id	
			).join(prf_query, prf_query.c.prf_user_id == Profesor.user_profesor_id	
			).join(Cliente, Cliente.id_cliente == Concertacion_Tema.conc_cliente_id	
			).join(cli_query, cli_query.c.cli_user_id == Cliente.user_cliente_id	
			).filter(Cliente.user_cliente_id == current_user.id
			).all()	 

	# Serializar los datos
	result = [
        {
			#Datos de Concertacion
			"id_conc_tema": tarea[0],
			"conc_tema": tarea[1],
			"conc_cliente_id": tarea[2],
			"conc_profesor_id": tarea[3],
			#Datos de profesor
			"id_profesor": tarea[4],			
			"prf_ci": tarea[5],
			"prf_nombre": tarea[6],
			"prf_primer_appellido": tarea[7],
			"prf_segundo_appellido": tarea[8],
			#Datos de cliente
			"id_cliente": tarea[9],
			"cli_user_id": tarea[10],
			"cli_nombre": tarea[11],
			"cli_primer_appellido": tarea[12],
			"cli_segundo_appellido": tarea[13],
			#Datos de estudiante
			"id_estudiante": tarea[14],
			"est_user_id": tarea[15],
			"est_nombre": tarea[16],
			"est_primer_appellido": tarea[17],
			"est_segundo_appellido": tarea[18],
			#Datos de Tarea
			"id_tarea": tarea[19],
			"concertacion_tarea_id": tarea[20],
			"tarea_activa": tarea[21],
			"tarea_asignada": tarea[22],
			"tarea_complejidad_estimada": tarea[23],
			"tarea_descripcion": tarea[24],
			"tarea_evaluacion": tarea[25],
			"tarea_evaluacion_pred": tarea[26],
			"tarea_fecha_fin": tarea[27],
			"tarea_fecha_inicio": tarea[28],
			"tarea_participantes": tarea[29],
			"tarea_tipo": tarea[30]
        }
        for tarea in db_tarea
    ] 
    
	return result

@router.get("/leer_tareas_profesor/", status_code=status.HTTP_201_CREATED)  
async def leer_tareas_profesor(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
        
	#Datos Profesor
	est_query = db.query(
		User.id.label('est_user_id'),
		User.nombre.label('est_nombre'),
		User.primer_appellido.label('est_primer_appellido'),
		User.segundo_appellido.label('est_segundo_appellido'),
	).select_from(
		User
	).subquery()

	#Datos Profesor
	prf_query = db.query(
		User.id.label('prf_user_id'),
		User.nombre.label('prf_nombre'),
		User.primer_appellido.label('prf_primer_appellido'),
		User.segundo_appellido.label('prf_segundo_appellido'),
	).select_from(
		User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		User.id.label('cli_user_id'),
		User.nombre.label('cli_nombre'),
		User.primer_appellido.label('cli_primer_appellido'),
		User.segundo_appellido.label('cli_segundo_appellido'),
	).select_from(
		User
	).subquery()	

	db_tarea = db.query(
			#Datos de Concertacion
			Concertacion_Tema.id_conc_tema,
			Concertacion_Tema.conc_tema,
			Concertacion_Tema.conc_cliente_id,
			Concertacion_Tema.conc_profesor_id,
			#Datos de profesor
			Profesor.id_profesor,			
			prf_query.c.prf_user_id,
			prf_query.c.prf_nombre,
			prf_query.c.prf_primer_appellido,
			prf_query.c.prf_segundo_appellido,
			#Datos de cliente
			Cliente.id_cliente,
			cli_query.c.cli_user_id,
			cli_query.c.cli_nombre,
			cli_query.c.cli_primer_appellido,
			cli_query.c.cli_segundo_appellido,
			#Datos de estudiante
			Estudiante.id_estudiante,
			est_query.c.est_user_id,
			est_query.c.est_nombre,
			est_query.c.est_primer_appellido,
			est_query.c.est_segundo_appellido,
			#Datos de tareas
			Tarea.id_tarea,
			Tarea.concertacion_tarea_id,
			Tarea.tarea_activa,
			Tarea.tarea_asignada,
			Tarea.tarea_complejidad_estimada,
			Tarea.tarea_descripcion,
			Tarea.tarea_evaluacion,
			Tarea.tarea_evaluacion_pred,
			Tarea.tarea_fecha_fin,
			Tarea.tarea_fecha_inicio,
			Tarea.tarea_participantes,
			Tarea.tarea_tipo
			).select_from(Tarea
			).join(Concertacion_Tema, Concertacion_Tema.id_conc_tema == Tarea.concertacion_tarea_id
		  	).join(Estudiante, Estudiante.tareas_estudiantes_id == Tarea.id_tarea
			).join(est_query, est_query.c.est_user_id == Estudiante.user_estudiante_id	
			).join(Profesor, Profesor.id_profesor == Concertacion_Tema.conc_profesor_id	
			).join(prf_query, prf_query.c.prf_user_id == Profesor.user_profesor_id	
			).join(Cliente, Cliente.id_cliente == Concertacion_Tema.conc_cliente_id	
			).join(cli_query, cli_query.c.cli_user_id == Cliente.user_cliente_id	
			).filter(Profesor.user_profesor_id == current_user.id
			).all()	 

	# Serializar los datos
	result = [
        {
			#Datos de Concertacion
			"id_conc_tema": tarea[0],
			"conc_tema": tarea[1],
			"conc_cliente_id": tarea[2],
			"conc_profesor_id": tarea[3],
			#Datos de profesor
			"id_profesor": tarea[4],			
			"prf_ci": tarea[5],
			"prf_nombre": tarea[6],
			"prf_primer_appellido": tarea[7],
			"prf_segundo_appellido": tarea[8],
			#Datos de cliente
			"id_cliente": tarea[9],
			"cli_user_id": tarea[10],
			"cli_nombre": tarea[11],
			"cli_primer_appellido": tarea[12],
			"cli_segundo_appellido": tarea[13],
			#Datos de estudiante
			"id_estudiante": tarea[14],
			"est_user_id": tarea[15],
			"est_nombre": tarea[16],
			"est_primer_appellido": tarea[17],
			"est_segundo_appellido": tarea[18],
			#Datos de Tarea
			"id_tarea": tarea[19],
			"concertacion_tarea_id": tarea[20],
			"tarea_activa": tarea[21],
			"tarea_asignada": tarea[22],
			"tarea_complejidad_estimada": tarea[23],
			"tarea_descripcion": tarea[24],
			"tarea_evaluacion": tarea[25],
			"tarea_evaluacion_pred": tarea[26],
			"tarea_fecha_fin": tarea[27],
			"tarea_fecha_inicio": tarea[28],
			"tarea_participantes": tarea[29],
			"tarea_tipo": tarea[30]
        }
        for tarea in db_tarea
    ] 
    
	return result	

@router.get("/leer_tareas/", status_code=status.HTTP_201_CREATED)  
async def leer_tareas(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	#Datos Profesor
	est_query = db.query(
		User.id.label('est_user_id'),
		User.nombre.label('est_nombre'),
		User.primer_appellido.label('est_primer_appellido'),
		User.segundo_appellido.label('est_segundo_appellido'),
	).select_from(
		User
	).subquery()

	#Datos Profesor
	prf_query = db.query(
		User.id.label('prf_user_id'),
		User.nombre.label('prf_nombre'),
		User.primer_appellido.label('prf_primer_appellido'),
		User.segundo_appellido.label('prf_segundo_appellido'),
	).select_from(
		User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		User.id.label('cli_user_id'),
		User.nombre.label('cli_nombre'),
		User.primer_appellido.label('cli_primer_appellido'),
		User.segundo_appellido.label('cli_segundo_appellido'),
	).select_from(
		User
	).subquery()	

	db_tarea = db.query(
			#Datos de Concertacion
			Concertacion_Tema.id_conc_tema,
			Concertacion_Tema.conc_tema,
			Concertacion_Tema.conc_cliente_id,
			Concertacion_Tema.conc_profesor_id,
			#Datos de profesor
			Profesor.id_profesor,			
			prf_query.c.prf_user_id,
			prf_query.c.prf_nombre,
			prf_query.c.prf_primer_appellido,
			prf_query.c.prf_segundo_appellido,
			#Datos de cliente
			Cliente.id_cliente,
			cli_query.c.cli_user_id,
			cli_query.c.cli_nombre,
			cli_query.c.cli_primer_appellido,
			cli_query.c.cli_segundo_appellido,
			#Datos de estudiante
			Estudiante.id_estudiante,
			est_query.c.est_user_id,
			est_query.c.est_nombre,
			est_query.c.est_primer_appellido,
			est_query.c.est_segundo_appellido,
			#Datos de tareas
			Tarea.id_tarea,
			Tarea.concertacion_tarea_id,
			Tarea.tarea_activa,
			Tarea.tarea_asignada,
			Tarea.tarea_complejidad_estimada,
			Tarea.tarea_descripcion,
			Tarea.tarea_evaluacion,
			Tarea.tarea_evaluacion_pred,
			Tarea.tarea_fecha_fin,
			Tarea.tarea_fecha_inicio,
			Tarea.tarea_participantes,
			Tarea.tarea_tipo
			).select_from(Tarea
			).join(Concertacion_Tema, Concertacion_Tema.id_conc_tema == Tarea.concertacion_tarea_id
		  	).join(Estudiante, Estudiante.tareas_estudiantes_id == Tarea.id_tarea
			).join(est_query, est_query.c.est_user_id == Estudiante.user_estudiante_id	
			).join(Profesor, Profesor.id_profesor == Concertacion_Tema.conc_profesor_id	
			).join(prf_query, prf_query.c.prf_user_id == Profesor.user_profesor_id	
			).join(Cliente, Cliente.id_cliente == Concertacion_Tema.conc_cliente_id	
			).join(cli_query, cli_query.c.cli_user_id == Cliente.user_cliente_id	
			).all()	 

	# Serializar los datos
	result = [
        {
			#Datos de Concertacion
			"id_conc_tema": tarea[0],
			"conc_tema": tarea[1],
			"conc_cliente_id": tarea[2],
			"conc_profesor_id": tarea[3],
			#Datos de profesor
			"id_profesor": tarea[4],			
			"prf_ci": tarea[5],
			"prf_nombre": tarea[6],
			"prf_primer_appellido": tarea[7],
			"prf_segundo_appellido": tarea[8],
			#Datos de cliente
			"id_cliente": tarea[9],
			"cli_user_id": tarea[10],
			"cli_nombre": tarea[11],
			"cli_primer_appellido": tarea[12],
			"cli_segundo_appellido": tarea[13],
			#Datos de estudiante
			"id_estudiante": tarea[14],
			"est_user_id": tarea[15],
			"est_nombre": tarea[16],
			"est_primer_appellido": tarea[17],
			"est_segundo_appellido": tarea[18],
			#Datos de Tarea
			"id_tarea": tarea[19],
			"concertacion_tarea_id": tarea[20],
			"tarea_activa": tarea[21],
			"tarea_asignada": tarea[22],
			"tarea_complejidad_estimada": tarea[23],
			"tarea_descripcion": tarea[24],
			"tarea_evaluacion": tarea[25],
			"tarea_evaluacion_pred": tarea[26],
			"tarea_fecha_fin": tarea[27],
			"tarea_fecha_inicio": tarea[28],
			"tarea_participantes": tarea[29],
			"tarea_tipo": tarea[30]
        }
        for tarea in db_tarea
    ] 
    
	return result	

@router.get("/prediccion_tarea/{id}", status_code=status.HTTP_201_CREATED)
async def prediccion_tarea(current_user: Annotated[User_InDB, Depends(get_current_user)],
					id: str, db: Session = Depends(get_db)):
	
	#Datos Estudiante
	est_query = db.query(
		User.id.label('est_user_id'),
		User.estado_civil.label('est_estadocivil'),
		User.genero.label('est_genero'),
		User.hijos.label('est_hijos'),
	).select_from(
		User
	).subquery()
	
	#Datos para predecir las actividades de tareas			
	db_tarea = db.query(
		#Datos de Concertacion
		Concertacion_Tema.conc_actores_externos,
		Concertacion_Tema.conc_complejidad,
		#Datos de estudiante
		Estudiante.est_becado,
		Estudiante.est_pos_tecnica_escuela,
		Estudiante.est_pos_tecnica_hogar,
		Estudiante.est_posibilidad_economica,
		Estudiante.est_trab_remoto,
		Estudiante.est_trabajo,
		#Datos de tareas
		Tarea.tarea_complejidad_estimada,
		Tarea.tarea_participantes,
		Tarea.tarea_tipo
		).select_from(Tarea
		).join(Concertacion_Tema, Concertacion_Tema.id_conc_tema == Tarea.concertacion_tarea_id
		).join(Estudiante, Estudiante.tareas_estudiantes_id == Tarea.id_tarea
		).join(est_query, est_query.c.est_user_id == Estudiante.user_estudiante_id	
		).join(Profesor, Profesor.id_profesor == Concertacion_Tema.conc_profesor_id	
		).join(Cliente, Cliente.id_cliente == Concertacion_Tema.conc_cliente_id	
		).where(Tarea.id_tarea == id
		).statement
				
	#Preparando datos
	datos = pd.read_sql(db_tarea, con=engine)
	#Leer modelo
	loaded_modelo = joblib.load(config.UPLOAD_TRAIN_MODELS_PATH + 'tarea_rf_model.pkl')
	#Realizar prediccion
	if datos.empty:
		raise HTTPException(status_code=404, detail="No existen ejemplos para predecir")
		
	prediccion = loaded_modelo.predict(datos)
	prob = loaded_modelo.predict_proba(datos)
	resdic = {
		"clase": prediccion[0],
		"prob1": prob[0][0],
		"prob2": prob[0][1]
	}

	return resdic