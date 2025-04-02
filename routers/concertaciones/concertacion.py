from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Concertacion_Tema, User, Profesor, Cliente
from schemas.concertacion import Concertacion_Record, ConcertacionAdd, Concertacion_InDB, Concertacion_Eval, Concertacion_Activate, Concertacion_Actores
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from schemas.user import User_InDB
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List
import pandas as pd
import pickle
from core import config
import numpy as np


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
		)			
		db.add(db_concertacion)   	
		db.commit()
		db.refresh(db_concertacion)			
		return db_concertacion
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Concertación")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error SQLAlchemy creando el objeto Concertación")		


@router.delete("/eliminar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_concertacion = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_concertacion is None:
		raise HTTPException(status_code=404, detail="La concertación no existe en la base de datos")	
	db.delete(db_concertacion)	
	db.commit()
	return {"Result": "Concertacion eliminada satisfactoriamente"}


@router.put("/actualizar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])], 
				id: str, concertacion: Concertacion_Record, db: Session = Depends(get_db)):
	
	db_conc = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_conc is None:
		raise HTTPException(status_code=404, detail="La concertación de tema seleccionada no existen en la base de datos")
	db_conc.conc_tema = concertacion.conc_tema
	db_conc.conc_descripcion = concertacion.conc_descripcion
	db_conc.conc_valoracion_prof = concertacion.conc_valoracion_prof
	db_conc.conc_valoracion_cliente = concertacion.conc_valoracion_prof
	db_conc.conc_complejidad = concertacion.conc_complejidad
	db_conc.conc_actores_externos = concertacion.conc_actores_externos
	db.commit()
	db.refresh(db_conc)	
	return {"Result": "Datos de la concertación de tema actualizados satisfactoriamente"}	
	

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
	

@router.put("/activar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def activar_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])], 
				id: str, concertacion: Concertacion_Activate, db: Session = Depends(get_db)):
	db_conc = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_conc is None:
		raise HTTPException(status_code=404, detail="La concertación de tema seleccionada no existen en la base de datos")	
	db_conc.conc_activa = concertacion.conc_activa
	db.commit()
	db.refresh(db_conc)	
	return {"Result": "Cambio de concertación desarrollada satisfactoriamente"}

@router.put("/evaluar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def evaluar_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor"])], 
				id: str, conc_eva: Concertacion_Eval, db: Session = Depends(get_db)):
	
	db_concertacion = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_concertacion is None:
		raise HTTPException(status_code=404, detail="Concertación no existe ne base de datos")
	db_concertacion.conc_evaluacion = conc_eva.conc_evaluacion 	
	db.commit()
	db.refresh(db_concertacion)	
	return db_concertacion
	

@router.get("/detalle_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def detalle_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor"])],
					id: str, db: Session = Depends(get_db)):
	db_concertacion = db.query(Concertacion_Tema).filter(Concertacion_Tema.id_conc_tema == id).first()
	if db_concertacion is None:
		raise HTTPException(status_code=404, detail="La concertación no existe en la base de datos")	

	return db_concertacion

#response_model=List[ProfesorSchema], 
@router.get("/leer_concertaciones/", status_code=status.HTTP_201_CREATED)  
async def leer_concertaciones_ext(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 

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

	db_conc = db.query(
			#Datos de Concertacion
			Concertacion_Tema.id_conc_tema,
			Concertacion_Tema.conc_tema,
			Concertacion_Tema.conc_descripcion,
			Concertacion_Tema.conc_valoracion_cliente,
			Concertacion_Tema.conc_valoracion_prof,
			Concertacion_Tema.conc_actores_externos,
			Concertacion_Tema.conc_cliente_id,
			Concertacion_Tema.conc_profesor_id,
			Concertacion_Tema.conc_complejidad,
			Concertacion_Tema.conc_evaluacion,
			Concertacion_Tema.conc_evaluacion_pred,
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
			).select_from(Concertacion_Tema
			).join(Profesor, Profesor.id_profesor == Concertacion_Tema.conc_profesor_id	
			).join(prf_query, prf_query.c.prf_user_id == Profesor.user_profesor_id	
			).join(Cliente, Cliente.id_cliente == Concertacion_Tema.conc_cliente_id	
			).join(cli_query, cli_query.c.cli_user_id == Cliente.user_cliente_id	
			).all()	 

	# Serializar los datos
	result = [
        {
			#Datos de Concertacion
			"id_conc_tema": concertaciones[0],
			"conc_tema": concertaciones[1],
			"conc_descripcion": concertaciones[2],
			"conc_valoracion_cliente": concertaciones[3],
			"conc_valoracion_prof": concertaciones[4],
			"conc_actores_externos": concertaciones[5],
			"conc_cliente_id": concertaciones[6],
			"conc_profesor_id": concertaciones[7],
			"conc_complejidad": concertaciones[8],
			"conc_evaluacion": concertaciones[9],
			"conc_evaluacion_pred": concertaciones[10],
			#Datos de profesor
			"id_profesor": concertaciones[11],			
			"prf_ci": concertaciones[12],
			"prf_nombre": concertaciones[13],
			"prf_primer_appellido": concertaciones[14],
			"prf_segundo_appellido": concertaciones[15],
			#Datos de cliente
			"id_cliente": concertaciones[16],
			"cli_user_id": concertaciones[17],
			"cli_nombre": concertaciones[18],
			"cli_primer_appellido": concertaciones[19],
			"cli_segundo_appellido": concertaciones[20],
        }
        for concertaciones in db_conc
    ] 
	
	return result

@router.get("/leer_concertaciones_profesor/", status_code=status.HTTP_201_CREATED)  
async def leer_concertaciones_profesor(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
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

	db_conc = db.query(
			#Datos de Concertacion
			Concertacion_Tema.id_conc_tema,
			Concertacion_Tema.conc_tema,
			Concertacion_Tema.conc_descripcion,
			Concertacion_Tema.conc_valoracion_cliente,
			Concertacion_Tema.conc_valoracion_prof,
			Concertacion_Tema.conc_actores_externos,
			Concertacion_Tema.conc_cliente_id,
			Concertacion_Tema.conc_profesor_id,
			Concertacion_Tema.conc_complejidad,
			Concertacion_Tema.conc_evaluacion,
			Concertacion_Tema.conc_evaluacion_pred,
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
			).select_from(Concertacion_Tema
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
			"id_conc_tema": concertaciones[0],
			"conc_tema": concertaciones[1],
			"conc_descripcion": concertaciones[2],
			"conc_valoracion_cliente": concertaciones[3],
			"conc_valoracion_prof": concertaciones[4],
			"conc_actores_externos": concertaciones[5],
			"conc_cliente_id": concertaciones[6],
			"conc_profesor_id": concertaciones[7],
			"conc_complejidad": concertaciones[8],
			"conc_evaluacion": concertaciones[9],
			"conc_evaluacion_pred": concertaciones[10],
			#Datos de profesor
			"id_profesor": concertaciones[11],			
			"prf_ci": concertaciones[12],
			"prf_nombre": concertaciones[13],
			"prf_primer_appellido": concertaciones[14],
			"prf_segundo_appellido": concertaciones[15],
			#Datos de cliente
			"id_cliente": concertaciones[16],
			"cli_user_id": concertaciones[17],
			"cli_nombre": concertaciones[18],
			"cli_primer_appellido": concertaciones[19],
			"cli_segundo_appellido": concertaciones[20],
        }
        for concertaciones in db_conc
    ] 
	
	return result

@router.get("/leer_concertaciones_cliente/", status_code=status.HTTP_201_CREATED)  
async def leer_concertaciones_cliente(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["cliente"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

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

	db_conc = db.query(
			#Datos de Concertacion
			Concertacion_Tema.id_conc_tema,
			Concertacion_Tema.conc_tema,
			Concertacion_Tema.conc_descripcion,
			Concertacion_Tema.conc_valoracion_cliente,
			Concertacion_Tema.conc_valoracion_prof,
			Concertacion_Tema.conc_actores_externos,
			Concertacion_Tema.conc_cliente_id,
			Concertacion_Tema.conc_profesor_id,
			Concertacion_Tema.conc_complejidad,
			Concertacion_Tema.conc_evaluacion,
			Concertacion_Tema.conc_evaluacion_pred,
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
			).select_from(Concertacion_Tema
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
			"id_conc_tema": concertaciones[0],
			"conc_tema": concertaciones[1],
			"conc_descripcion": concertaciones[2],
			"conc_valoracion_cliente": concertaciones[3],
			"conc_valoracion_prof": concertaciones[4],
			"conc_actores_externos": concertaciones[5],
			"conc_cliente_id": concertaciones[6],
			"conc_profesor_id": concertaciones[7],
			"conc_complejidad": concertaciones[8],
			"conc_evaluacion": concertaciones[9],
			"conc_evaluacion_pred": concertaciones[10],
			#Datos de profesor
			"id_profesor": concertaciones[11],			
			"prf_ci": concertaciones[12],
			"prf_nombre": concertaciones[13],
			"prf_primer_appellido": concertaciones[14],
			"prf_segundo_appellido": concertaciones[15],
			#Datos de cliente
			"id_cliente": concertaciones[16],
			"cli_user_id": concertaciones[17],
			"cli_nombre": concertaciones[18],
			"cli_primer_appellido": concertaciones[19],
			"cli_segundo_appellido": concertaciones[20],
        }
        for concertaciones in db_conc
    ] 
	return result 

@router.get("/prediccion_concertacion/{id}", status_code=status.HTTP_201_CREATED)
async def prediccion_concertacion(current_user: Annotated[User_InDB, Depends(get_current_user)],
					id: str, db: Session = Depends(get_db)):
	
	prf_query = db.query(
		User.id.label('prf_user_id'),
		User.estado_civil.label('prf_estadocivil'),
		User.genero.label('prf_genero'),
		User.hijos.label('prf_hijos'),
	).select_from(
		User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		User.id.label('cli_user_id'),
		User.estado_civil.label('cli_estadocivil'),
		User.genero.label('cli_genero'),
		User.hijos.label('cli_hijos'),
	).select_from(
		User
	).subquery()	

	db_conc = db.query(
		#Datos de Concertacion
		Concertacion_Tema.conc_actores_externos,
		Concertacion_Tema.conc_complejidad,
		#Datos de profesor		
		Profesor.prf_trab_remoto,
		Profesor.prf_cargo,
		Profesor.prf_categoria_cientifica,
		Profesor.prf_categoria_docente,
		Profesor.prf_pos_tecnica_trabajo,
		Profesor.prf_pos_tecnica_hogar,
		Profesor.prf_experiencia_practicas,
		Profesor.prf_numero_empleos,
		Profesor.prf_numero_est_atendidos,
		#Datos de cliente
		Cliente.cli_cargo,
		Cliente.cli_categoria_cientifica,
		Cliente.cli_categoria_docente,
		Cliente.cli_experiencia_practicas,
		Cliente.cli_numero_empleos,
		Cliente.cli_numero_est_atendidos,
		Cliente.cli_pos_tecnica_hogar,
		Cliente.cli_pos_tecnica_trabajo,
		Cliente.cli_trab_remoto,
		).select_from(Concertacion_Tema
		).join(Profesor, Profesor.id_profesor == Concertacion_Tema.conc_profesor_id	
		).join(prf_query, prf_query.c.prf_user_id == Profesor.user_profesor_id	
		).join(Cliente, Cliente.id_cliente == Concertacion_Tema.conc_cliente_id	
		).join(cli_query, cli_query.c.cli_user_id == Cliente.user_cliente_id	
		).where(Concertacion_Tema.id_conc_tema == id
		).statement
	
	"""
		
		prf_query.c.prf_estadocivil,
		prf_query.c.prf_genero,
		prf_query.c.prf_hijos,
		
		cli_query.c.cli_estadocivil,
		cli_query.c.cli_genero,
		cli_query.c.cli_hijos,
		"""
	
	#Preparando datos
	datos = pd.read_sql(db_conc, con=engine)
	print(datos.columns)
	#Leer modelo
	with open(config.UPLOAD_TRAIN_MODELS_PATH + 'conc_rf_model.pkl', 'rb') as f:
		loaded_modelo = pickle.load(f)
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
	
	#return {"clase": "Mejorable"}




