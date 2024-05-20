from fastapi import Depends, FastAPI, HTTPException, status, Response, Security, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from functools import lru_cache
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import case
from sqlalchemy import desc, asc
from uuid import uuid4
from pathlib import Path
from typing import Union
from datetime import datetime, timedelta
#---Imported for JWT example-----------
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
from typing_extensions import Annotated
import models
import schemas
from database import SessionLocal, engine 
import init_db
import config
import asyncio
import concurrent.futures
import csv
from io import BytesIO, StringIO
from fastapi.responses import StreamingResponse
#FOR MACHONE LEARNING
#import numpy as np
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OrdinalEncoder, MinMaxScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.compose import make_column_selector
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
import joblib
import json

models.Base.metadata.create_all(bind=engine)

#Create resources for JWT flow
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
	tokenUrl="token",
	scopes={"admin": "Add, edit and delete information.", "profesor": "Create and read information.", "cliente": "Create and read information.", "estudiante": "Create and read information.", "usuario": "Only read information"}
)
#----------------------
#Create our main app
app = FastAPI()

#----SETUP MIDDLEWARES--------------------

# Allow these origins to access the API
origins = [	
	"http://practicasprofesionales.onrender.com",
	"https://practicasprofesionales.onrender.com",		
	"http://localhost",
	"http://localhost:8080",
	"https://localhost:8080",
	"http://localhost:5000",
	"https://localhost:5000",
	"http://localhost:3000",
	"https://localhost:3000",
	"http://localhost:8000",
	"https://localhost:8000",
]

# Allow these methods to be used
methods = ["GET", "POST", "PUT", "DELETE"]

# Only these headers are allowed
headers = ["Content-Type", "Authorization"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=methods,
	allow_headers=headers,
	expose_headers=["*"]
)

ALGORITHM = config.ALGORITHM	
SECRET_KEY = config.SECRET_KEY
APP_NAME = config.APP_NAME
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES
ADMIN_USER = config.ADMIN_USER
ADMIN_NOMBRE = config.ADMIN_NOMBRE
ADMIN_PAPELLIDO = config.ADMIN_PAPELLIDO
ADMIN_SAPELLIDO = config.ADMIN_SAPELLIDO
ADMIN_CI = config.ADMIN_CI
ADMIN_CORREO = config.ADMIN_CORREO
ADMIN_PASS = config.ADMIN_PASS

# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


#------CODE FOR THE JWT EXAMPLE----------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
	db_user = db.query(models.User).filter(models.User.username == username).first()	
	if db_user is not None:
		return db_user 

#This function is used by "login_for_access_token"
def authenticate_user(username: str, password: str,  db: Session = Depends(get_db)):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password): #secret
        return False
    return user
	
#This function is used by "login_for_access_token"
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30) #Si no se pasa un valor por usuario
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
	
#This function is used by "get currecnt active user" dependency security authentication
async def get_current_user(
			security_scopes: SecurityScopes, 
			token: Annotated[str, Depends(oauth2_scheme)],
			db: Session = Depends(get_db)):
	if security_scopes.scopes:
		authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
	else:
		authenticate_value = "Bearer"
		
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username: str = payload.get("sub")
		if username is None:
			raise credentials_exception			
		token_scopes = payload.get("scopes", [])
		token_data = schemas.TokenData(scopes=token_scopes, username=username)
		
	except (JWTError, ValidationError):
		raise credentials_exception
			
		token_data = schemas.TokenData(username=username)
	except JWTError:
		raise credentials_exception
		
	user = get_user(db, username=token_data.username)
	if user is None:
		raise credentials_exception
		
	for user_scope in security_scopes.scopes:
		if user_scope not in token_data.scopes:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Not enough permissions",
				headers={"WWW-Authenticate": authenticate_value},
			)
			
	return user
	
async def get_current_active_user(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["admin"])]):  #, "manager", "user"
	if current_user.disable:
		print({"USER AUTENTICATED" : current_user.disable})
		print({"USER ROLES" : current_user.role})
		raise HTTPException(status_code=400, detail="Disable user")
	return current_user

#------------------------------------
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
	user = authenticate_user(form_data.username, form_data.password, db)
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"},
		)
	access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
	print(form_data.scopes)
	
	print(user.role) #Prin my roles to confirm them
	
	access_token = create_access_token(
		data={"sub": user.username, "scopes": user.role},   #form_data.scopes
		expires_delta=access_token_expires
	)
	return {"detail": "Ok", "access_token": access_token, "token_type": "Bearer"}
	
@app.get("/")
def index():
	return {"Application": "Hello from developers"}
	
@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: Annotated[schemas.User, Depends(get_current_user)]):
	return current_user

@app.get("/get_restricted_user")
async def get_restricted_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)]):
    return current_user
	
@app.get("/get_authenticated_admin_resources", response_model=schemas.User)
async def get_authenticated_admin_resources(current_user: Annotated[schemas.User, Security(get_current_active_user, scopes=["profesor"])]):
    return current_user
	
@app.get("/get_authenticated_edition_resources", response_model=schemas.User)
async def get_authenticated_edition_resources(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])]):
    return current_user
	
	
#########################
###   USERS ADMIN  ######
#########################
@app.post("/create_owner", status_code=status.HTTP_201_CREATED)  
async def create_owner(db: Session = Depends(get_db)): #Por el momento no tiene restricciones
	if db.query(models.User).filter(models.User.username == config.ADMIN_USER).first():
		db_user = db.query(models.User).filter(models.User.username == config.ADMIN_USER).first()
		if db_user is None:
			raise HTTPException(status_code=404, detail="User not found")	
		db.delete(db_user)	
		db.commit()
		
	db_user = models.User(
		username=config.ADMIN_USER, 
		nombre=config.ADMIN_NOMBRE,
		primer_appellido=config.ADMIN_PAPELLIDO,
		segundo_appellido=config.ADMIN_SAPELLIDO,
		ci=config.ADMIN_CI,
		email=config.ADMIN_CORREO,
		role=["admin","profesor","cliente","estudiante","usuario"],
		disable=False,
		hashed_password=pwd_context.hash(config.ADMIN_PASS)		
	)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)	
	return {f"User:": "Succesfully created"}
	
@app.post("/create_user/", status_code=status.HTTP_201_CREATED)  
async def create_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				user: schemas.UserAdd, db: Session = Depends(get_db)): 
	if db.query(models.User).filter(models.User.username == user.username).first() :
		raise HTTPException( 
			status_code=400,
			detail="The user with this email already exists in the system",
		)	
	db_user = models.User(
		username=user.username, 
		nombre=user.nombre,
		primer_appellido=user.primer_appellido,
		segundo_appellido=user.segundo_appellido,
		ci=user.ci,
		email=user.email,
		role=user.role,
		disable=True,
		hashed_password=pwd_context.hash(user.hashed_password)
	)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)	
	return {f"User: {db_user.username}": "Succesfully created"}
	
@app.get("/read_users/", status_code=status.HTTP_201_CREATED) 
async def read_users(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
		skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    	
	db_users = db.query(models.User).offset(skip).limit(limit).all()    
	return db_users
	

@app.put("/update_user/{username}", status_code=status.HTTP_201_CREATED) 
async def update_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)], 
				username: str, new_user: schemas.UserUPD, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="User not found")
	db_user.nombre=new_user.nombre	
	db_user.primer_appellido=new_user.primer_appellido
	db_user.segundo_appellido=new_user.segundo_appellido
	db_user.ci=new_user.ci	
	db_user.email=new_user.email	
	db_user.role=new_user.role
	db.commit()
	db.refresh(db_user)	
	return db_user	
	
@app.put("/activate_user/{username}", status_code=status.HTTP_201_CREATED) 
async def activate_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				username: str, new_user: schemas.UserActivate, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="User not found")
	if username != "_admin" and username != current_user.username:
		db_user.disable=new_user.disable		
		db.commit()
		db.refresh(db_user)	
	return db_user	
	
@app.delete("/delete_user/{username}", status_code=status.HTTP_201_CREATED) 
async def delete_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				username: str, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="User not found")	
	if username != "_admin" and username != current_user.username:
		db.delete(db_user)	
		db.commit()
	return {"Deleted": "Delete User Successfuly"}
	
@app.put("/reset_password/{username}", status_code=status.HTTP_201_CREATED) 
async def reset_password(current_user: Annotated[schemas.User, Security(get_current_user, scopes=[ "profesor", "cliente", "estudiante"])],
				username: str, password: schemas.UserPassword, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="User not found")	
	db_user.hashed_password=pwd_context.hash(password.hashed_password)
	db.commit()
	db.refresh(db_user)	
	return {"Result": "Password Updated Successfuly"}
	
@app.put("/reset_password_by_user/{username}", status_code=status.HTTP_201_CREATED) 
async def reset_password_by_user(current_user: Annotated[schemas.User, Security(get_current_user, scopes=[ "profesor", "cliente", "estudiante"])],
				username: str, password: schemas.UserResetPassword, db: Session = Depends(get_db)):
				
	if not verify_password(password.actualpassword, current_user.hashed_password): 
		return HTTPException(status_code=700, detail="Actual password doesn't match")
		
	db_user = db.query(models.User).filter(models.User.username == username).first()	
	if db_user is None:
		raise HTTPException(status_code=404, detail="User not found")	
	db_user.hashed_password=pwd_context.hash(password.newpassword)
	db.commit()
	db.refresh(db_user)	
	return {"response": "Password Updated Successfuly"}
		
#############################
####  ENTIDAD ORIGEN  #######
#############################
@app.post("/crear_entidad_origen/", status_code=status.HTTP_201_CREATED)
async def crear_entidad_origen(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					ent_origen: schemas.Entidad_Origen, db: Session = Depends(get_db)):
	try:
		db_ent_origen = models.Entidad_Origen(
			org_nombre = ent_origen.org_nombre,
			org_siglas = ent_origen.org_siglas,
			org_nivel_tecnologico = ent_origen.org_nivel_tecnologico,
			org_transporte = ent_origen.org_transporte,
			org_trab_remoto = ent_origen.org_trab_remoto
		)			
		db.add(db_ent_origen)   	
		db.commit()
		db.refresh(db_ent_origen)			
		return db_ent_origen
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Entidad origen")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Entidad origen")		

@app.get("/leer_entidades_origen/", status_code=status.HTTP_201_CREATED)  
async def leer_entidades_origen(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_entidades = db.query(models.Entidad_Origen).all()	
	
	return db_entidades
	
@app.delete("/eliminar_entidad_origen/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_entidad_origen(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	db_entidad = db.query(models.Entidad_Origen
						).filter(models.Entidad_Origen.id_entidad_origen == id
						).first()
	if db_entidad is None:
		raise HTTPException(status_code=404, detail="La Entidad Origen no existe en la base de datos")	
	db.delete(db_entidad)	
	db.commit()
	return {"Result": "Entidad origen eliminada satisfactoriamente"}
	
@app.put("/actualizar_entidad_origen/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_entidad_origen(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, entidad_nueva: schemas.Entidad_Origen, db: Session = Depends(get_db)):
	
	db_entidad_origen = db.query(models.Entidad_Origen).filter(models.Entidad_Origen.id_entidad_origen == id).first()
	
	if db_entidad_origen is None:
		raise HTTPException(status_code=404, detail="La entidad seleccionada no existen en la base de datos")
	
	db_entidad_origen.org_nombre=entidad_nueva.org_nombre
	db_entidad_origen.org_siglas=entidad_nueva.org_siglas
	db_entidad_origen.org_nivel_tecnologico=entidad_nueva.org_nivel_tecnologico	
	db_entidad_origen.org_transporte=entidad_nueva.org_transporte
	db_entidad_origen.org_trab_remoto=entidad_nueva.org_trab_remoto
	
	db.commit()
	db.refresh(db_entidad_origen)	
	return {"Result": "Entidad origen actualizada satisfactoriamente"}	
	
#############################
####  ENTIDAD DESTINO #######
#############################
@app.post("/crear_entidad_destino/", status_code=status.HTTP_201_CREATED)
async def crear_entidad_destino(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					ent_destino: schemas.Entidad_Destino, db: Session = Depends(get_db)):
	try:
		db_ent_destino = models.Entidad_Destino(
			dest_nombre = ent_destino.dest_nombre,
			dest_siglas = ent_destino.dest_siglas,
			dest_nivel_tecnologico = ent_destino.dest_nivel_tecnologico,
			dest_transporte = ent_destino.dest_transporte,
			dest_experiencia = ent_destino.dest_experiencia,
			dest_trab_remoto = ent_destino.dest_trab_remoto
		)			
		db.add(db_ent_destino)   	
		db.commit()
		db.refresh(db_ent_destino)			
		return db_ent_destino
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Entidad_destino")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Entidad_destino")		

@app.get("/leer_entidades_destino/", status_code=status.HTTP_201_CREATED)  
async def leer_entidades_destino(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_entidades = db.query(models.Entidad_Destino).all()	
	
	return db_entidades
	
@app.delete("/eliminar_entidad_destino/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_entidad_destino(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	db_entidad = db.query(models.Entidad_Destino
						).filter(models.Entidad_Destino.id_entidad_destino == id
						).first()
	if db_entidad is None:
		raise HTTPException(status_code=404, detail="La Entidad Destino no existe en la base de datos")	
	db.delete(db_entidad)	
	db.commit()
	return {"Result": "Entidad destino eliminada satisfactoriamente"}
	
@app.put("/actualizar_entidad_destino/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_entidad_destino(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, entidad_nueva: schemas.Entidad_Destino, db: Session = Depends(get_db)):
	
	db_entidad_destino = db.query(models.Entidad_Destino).filter(models.Entidad_Destino.id_entidad_destino == id).first()
	
	if db_entidad_destino is None:
		raise HTTPException(status_code=404, detail="La entidad seleccionada no existen en la base de datos")
	
	db_entidad_destino.dest_nombre=entidad_nueva.dest_nombre
	db_entidad_destino.dest_siglas=entidad_nueva.dest_siglas
	db_entidad_destino.dest_nivel_tecnologico=entidad_nueva.dest_nivel_tecnologico	
	db_entidad_destino.dest_transporte=entidad_nueva.dest_transporte
	db_entidad_destino.dest_trab_remoto=entidad_nueva.dest_trab_remoto
	db_entidad_destino.dest_experiencia=entidad_nueva.dest_experiencia
	
	db.commit()
	db.refresh(db_entidad_destino)	
	return {"Result": "Entidad Destino actualizada satisfactoriamente"}	
	
#############################
#######  PROFESOR  ##########
#############################
@app.post("/crear_profesor/", status_code=status.HTTP_201_CREATED)
async def crear_profesor(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					profesor: schemas.Profesor, db: Session = Depends(get_db)):
	try:
		db_profesor = models.Profesor(
			prf_genero = profesor.prf_genero,
			prf_estado_civil = profesor.prf_estado_civil,  #Soltero, Casado, Divorciado, Viudo
			prf_numero_empleos = profesor.prf_numero_empleos,
			prf_hijos = profesor.prf_hijos,
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
		#db.refresh(db_profesor)	

		#Disable el profesor 
		db_user = db.query(models.User).filter(models.User.id == profesor.user_profesor_id).first()
		db_user.disable = False
		db.commit()
		
		db.refresh(db_user)	
		
		return db_profesor
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Profesor")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Profesor")		

@app.get("/leer_profesores/", status_code=status.HTTP_201_CREATED)  
async def leer_profesores(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	db_profesores = db.query(
							#Datos Profesor
							models.Profesor.id_profesor,
							models.Profesor.prf_genero,
							models.Profesor.prf_estado_civil,
							models.Profesor.prf_numero_empleos,
							models.Profesor.prf_hijos,
							models.Profesor.prf_pos_tecnica_trabajo,
							models.Profesor.prf_pos_tecnica_hogar,
							models.Profesor.prf_cargo,
							models.Profesor.prf_trab_remoto,
							models.Profesor.prf_categoria_docente,
							models.Profesor.prf_categoria_cientifica,
							models.Profesor.prf_experiencia_practicas,
							models.Profesor.prf_numero_est_atendidos,
							models.Profesor.prf_entidad_id.label('profesor_entidad'),
							#Datos Entidad Origen
							models.Entidad_Origen.org_siglas,
							models.Entidad_Origen.id_entidad_origen,
							#Datos del usiario
							models.User.ci,
							models.User.nombre,
							models.User.primer_appellido,
							models.User.segundo_appellido,
							models.User.email,							
							).select_from(models.Profesor
							).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
							).join(models.User, models.User.id == models.Profesor.user_profesor_id							
							).all()		
	
	return db_profesores
	
@app.get("/leer_profesores_no_activos/", status_code=status.HTTP_201_CREATED)  
async def leer_profesores_no_activos(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 
					
	db_profesores = db.query(
			models.User.id,
			models.User.ci,
			models.User.nombre,
			models.User.primer_appellido,
			models.User.segundo_appellido,
			models.User.email,							
		).select_from(models.User
		).where(models.User.role.contains("profesor")
		).filter_by(disable = True
		).all()		

	return db_profesores
	
@app.delete("/eliminar_profesor/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_profesor(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	db_profesor = db.query(models.Profesor
						).filter(models.Profesor.id_profesor == id
						).first()
	if db_profesor is None:
		raise HTTPException(status_code=404, detail="El profesor no existe en la base de datos")		
		
	#Disable el profesor 
	db_user = db.query(models.User).filter(models.User.id == db_profesor.user_profesor_id).first()
	db_user.disable = True	
	db.refresh(db_user)		
	
	db.delete(db_profesor)	
	db.commit()
	db.refresh(db_profesor)		
	
	return {"Result": "Profesor eliminado satisfactoriamente"}
	
@app.put("/actualizar_profesor/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_profesor(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, profesor: schemas.Profesor_UPD, db: Session = Depends(get_db)):
				
	db_profesor = db.query(models.Profesor).filter(models.Profesor.id_profesor == id).first()
	
	if db_profesor is None:
		raise HTTPException(status_code=404, detail="El profesor seleccionado no existen en la base de datos")
		
	db_profesor.prf_genero = profesor.prf_genero
	db_profesor.prf_estado_civil = profesor.prf_estado_civil
	db_profesor.prf_numero_empleos = profesor.prf_numero_empleos
	db_profesor.prf_hijos = profesor.prf_hijos
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

#############################
#######  ESTUDIANTE  ########
#############################
@app.post("/crear_estudiante/", status_code=status.HTTP_201_CREATED)
async def crear_estudiante(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					estudiante: schemas.Estudiante, db: Session = Depends(get_db)):
	try:
		db_estudiante = models.Estudiante(
			est_genero = estudiante.est_genero,
			est_estado_civil = estudiante.est_estado_civil,  #Soltero, Casado, Divorciado, Viudo
			est_trabajo = estudiante.est_trabajo, 
			est_becado = estudiante.est_becado, 
			est_hijos = estudiante.est_hijos,
			est_posibilidad_economica = estudiante.est_posibilidad_economica, 
			est_pos_tecnica_escuela = estudiante.est_pos_tecnica_escuela,
			est_pos_tecnica_hogar = estudiante.est_pos_tecnica_hogar,
			est_trab_remoto = estudiante.est_trab_remoto,
			est_entidad_id = estudiante.est_entidad_id,	
			user_estudiante_id = estudiante.user_estudiante_id
		)			
		db.add(db_estudiante)   	
		db.commit()
		db.refresh(db_estudiante)

		#Disable el estudiante 
		db_user = db.query(models.User).filter(models.User.id == estudiante.user_estudiante_id).first()
		db_user.disable = False
		db.commit()
		db.refresh(db_user)	
		
		return db_estudiante
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Estudiante")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Estudiante")		

@app.get("/leer_estudiante_simple/", status_code=status.HTTP_201_CREATED)  
async def leer_estudiante_simple(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

		db_estudiantes = db.query(models.Estudiante).all()
		
		return db_estudiantes
		
@app.get("/leer_estudiantes/", status_code=status.HTTP_201_CREATED)  
async def leer_estudiantes(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	db_estudiantes = db.query(
							#Datos Estudiante
							models.Estudiante.id_estudiante,
							models.Estudiante.est_genero,
							models.Estudiante.est_estado_civil,
							models.Estudiante.est_trabajo,
							models.Estudiante.est_becado,
							models.Estudiante.est_hijos,
							models.Estudiante.est_posibilidad_economica,
							models.Estudiante.est_pos_tecnica_escuela,
							models.Estudiante.est_pos_tecnica_hogar,
							models.Estudiante.est_trab_remoto,
							models.Estudiante.est_entidad_id.label('estudiante_entidad'),
							#Datos Entidad Origen
							models.Entidad_Origen.org_siglas,
							models.Entidad_Origen.id_entidad_origen,
							#Datos del usiario
							models.User.ci,
							models.User.nombre,
							models.User.primer_appellido,
							models.User.segundo_appellido,
							models.User.email,				
							).select_from(models.Estudiante
							).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Estudiante.est_entidad_id
							).join(models.User, models.User.id == models.Estudiante.user_estudiante_id	
							).all()		
	
	return db_estudiantes
	
@app.get("/leer_estudiantes_no_activos/", status_code=status.HTTP_201_CREATED)  
async def leer_estudiantes_no_activos(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 
					
	db_estudiantes = db.query(
			models.User.id,
			models.User.ci,
			models.User.nombre,
			models.User.primer_appellido,
			models.User.segundo_appellido,
			models.User.email,							
		).select_from(models.User
		).where(models.User.role.contains("estudiante")
		).filter_by(disable = True
		).all()		

	return db_estudiantes
	
@app.get("/leer_estudiante_tarea_por_email/{email}", status_code=status.HTTP_201_CREATED)  
async def leer_estudiante_tarea_por_email(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["estudiante"])],
					email: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 
					
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.ci.label('est_ci'),
		models.User.nombre.label('est_nombre'),
		models.User.primer_appellido.label('est_primer_appellido'),
		models.User.segundo_appellido.label('est_segundo_appellido'),
		models.User.email.label('est_email'),	
	).select_from(models.User
	).where(models.User.email == email
	).subquery()	
	
	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.ci.label('prf_ci'),
		models.User.nombre.label('prf_nombre'),
		models.User.primer_appellido.label('prf_primer_appellido'),
		models.User.segundo_appellido.label('prf_segundo_appellido'),
		models.User.email.label('prf_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.ci.label('cli_ci'),
		models.User.nombre.label('cli_nombre'),
		models.User.primer_appellido.label('cli_primer_appellido'),
		models.User.segundo_appellido.label('cli_segundo_appellido'),
		models.User.email.label('cli_email'),	
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las asignaciones
	db_estuduante_asgnaciones_tarea = db.query(
		#Datos de Asignacion
		models.Asignacion_Tarea.id_asignacion,
		models.Asignacion_Tarea.asg_descripcion,
		models.Asignacion_Tarea.asg_fecha_inicio,
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		models.Asignacion_Tarea.asg_evaluacion,
		models.Asignacion_Tarea.asg_tipo_tarea_id,
		models.Asignacion_Tarea.asg_estudiante_id,
		models.Asignacion_Tarea.asg_conc_id,
		models.Asignacion_Tarea.asg_activa,
		#Datos Tipo de tarea
		models.Tipo_Tarea.id_tipo_tarea,
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema,
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_profesor_id,						
		models.Concertacion_Tema.conc_cliente_id,
		#Datos de Estudiante
		models.Estudiante.id_estudiante,
		models.Estudiante.est_entidad_id,
		est_query.c.est_ci,
		est_query.c.est_nombre,
		est_query.c.est_primer_appellido,
		est_query.c.est_segundo_appellido,
		est_query.c.est_email,		
		#Datos de profesor
		models.Profesor.id_profesor,			
		prf_query.c.prf_ci,
		prf_query.c.prf_nombre,
		prf_query.c.prf_primer_appellido,
		prf_query.c.prf_segundo_appellido,
		prf_query.c.prf_email,		
		models.Profesor.prf_entidad_id,
		#Datos de cliente
		models.Cliente.id_cliente,
		cli_query.c.cli_ci,
		cli_query.c.cli_nombre,
		cli_query.c.cli_primer_appellido,
		cli_query.c.cli_segundo_appellido,
		cli_query.c.cli_email,		
		models.Cliente.cli_entidad_id,
		).select_from(models.Asignacion_Tarea
		).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
		).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
		).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id	
		).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id	
		).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Estudiante.est_entidad_id	
		).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id	
		).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
		).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id	
		).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id	
		).first()		

	return db_estuduante_asgnaciones_tarea
	
@app.delete("/eliminar_estudiante/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_estudiante(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	db_estudiante = db.query(models.Estudiante
						).filter(models.Estudiante.id_estudiante == id
						).first()
	if db_estudiante is None:
		raise HTTPException(status_code=404, detail="El estudiante no existe en la base de datos")	
		
	#Disable el estudiante
	db_user = db.query(models.User).filter(models.User.id == db_estudiante.user_estudiante_id).first()
	db_user.disable = True
	db.refresh(db_user)	
	
	db.delete(db_estudiante)	
	db.commit()
	db.refresh(db_estudiante)	
	
	return {"Result": "Estudiante eliminado satisfactoriamente"}
	
@app.put("/actualizar_estudiante/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_estudiante(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])], 
				id: str, estudiante: schemas.Estudiante_UPD, db: Session = Depends(get_db)):
	
	db_estudiante = db.query(models.Estudiante).filter(models.Estudiante.id_estudiante == id).first()
	
	if db_estudiante is None:
		raise HTTPException(status_code=404, detail="El profesor seleccionado no existen en la base de datos")
		
	db_estudiante.est_genero = estudiante.est_genero
	db_estudiante.est_estado_civil = estudiante.est_estado_civil
	db_estudiante.est_trabajo = estudiante.est_trabajo
	db_estudiante.est_becado = estudiante.est_becado
	db_estudiante.est_hijos = estudiante.est_hijos
	db_estudiante.est_posibilidad_economica = estudiante.est_posibilidad_economica
	db_estudiante.est_pos_tecnica_escuela = estudiante.est_pos_tecnica_escuela
	db_estudiante.est_pos_tecnica_hogar = estudiante.est_pos_tecnica_hogar
	db_estudiante.est_trab_remoto = estudiante.est_trab_remoto	
	
	db.commit()
	db.refresh(db_estudiante)	
	return {"Result": "Datos del estudiante actualizados satisfactoriamente"}	

#############################
#######   CLIENTE  ##########
#############################
@app.post("/crear_cliente/", status_code=status.HTTP_201_CREATED)
async def crear_cliente(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					cliente: schemas.Cliente, db: Session = Depends(get_db)):
	try:
		db_cliente = models.Cliente(
			cli_genero = cliente.cli_genero,
			cli_estado_civil = cliente.cli_estado_civil,  #Soltero, Casado, Divorciado
			cli_numero_empleos = cliente.cli_numero_empleos,
			cli_hijos = cliente.cli_hijos, 
			cli_pos_tecnica_trabajo = cliente.cli_pos_tecnica_trabajo,
			cli_pos_tecnica_hogar = cliente.cli_pos_tecnica_hogar,
			cli_cargo = cliente.cli_cargo,
			cli_trab_remoto = cliente.cli_trab_remoto,
			cli_categoria_docente = cliente.cli_categoria_docente, #Instructor, Auxiliar, Asistente, Titular
			cli_categoria_cientifica = cliente.cli_categoria_cientifica, #Ingeniero, Licenciado, Master, Doctor, Tecnico
			cli_experiencia_practicas = cliente.cli_experiencia_practicas,  
			cli_numero_est_atendidos = cliente.cli_numero_est_atendidos,  #Numero de estudiantes atendidos en el pasado
			cli_entidad_id = cliente.cli_entidad_id,
			user_cliente_id = cliente.user_cliente_id			
		)			
		db.add(db_cliente)   	
		db.commit()
		db.refresh(db_cliente)

		#Disable el cliente 
		db_user = db.query(models.User).filter(models.User.id == cliente.user_cliente_id).first()
		db_user.disable = False
		db.commit()
		db.refresh(db_user)	
		
		return db_cliente 
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Cliente")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Cliente")		

@app.get("/leer_cliente_simple/", status_code=status.HTTP_201_CREATED)  
async def leer_cliente_simple(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

		db_cliente = db.query(models.Cliente).all()
		
		return db_cliente
		
@app.get("/leer_clientes/", status_code=status.HTTP_201_CREATED)  
async def leer_clientes(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_cliente = db.query(models.Cliente).all()

	db_cliente = db.query(
					#Datos Cliente
					models.Cliente.id_cliente,
					models.Cliente.cli_genero,
					models.Cliente.cli_estado_civil,
					models.Cliente.cli_numero_empleos,
					models.Cliente.cli_hijos,
					models.Cliente.cli_pos_tecnica_trabajo,
					models.Cliente.cli_pos_tecnica_hogar,
					models.Cliente.cli_cargo,
					models.Cliente.cli_trab_remoto,
					models.Cliente.cli_categoria_docente,
					models.Cliente.cli_categoria_cientifica,
					models.Cliente.cli_experiencia_practicas,
					models.Cliente.cli_numero_est_atendidos,
					models.Cliente.cli_entidad_id.label('cliente_entidad'),
					#Datos Entidad Destino
					models.Entidad_Destino.dest_siglas,
					models.Entidad_Destino.id_entidad_destino,
					#Datos del usiario
					models.User.ci,
					models.User.nombre,
					models.User.primer_appellido,
					models.User.segundo_appellido,
					models.User.email,		
					).select_from(models.Cliente
					).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id
					).join(models.User, models.User.id == models.Cliente.user_cliente_id	
					).all()			
	
	return db_cliente
	
@app.get("/leer_clientes_no_activos/", status_code=status.HTTP_201_CREATED)  
async def leer_clientes_no_activos(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 
					
	db_clientes = db.query(
			models.User.id,
			models.User.ci,
			models.User.nombre,
			models.User.primer_appellido,
			models.User.segundo_appellido,
			models.User.email,							
		).select_from(models.User
		).where(models.User.role.contains("cliente")
		).filter_by(disable = True
		).all()		

	return db_clientes
	
@app.delete("/eliminar_cliente/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_cliente(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	db_cliente = db.query(models.Cliente
						).filter(models.Cliente.id_cliente == id
						).first()
	if db_cliente is None:
		raise HTTPException(status_code=404, detail="El cliente no existe en la base de datos")	
		
	#Disable el cliente
	db_user = db.query(models.User).filter(models.User.id == db_cliente.user_cliente_id).first()
	db_user.disable = True
	db.refresh(db_user)	
	
	db.delete(db_cliente)	
	db.commit()
	db.refresh(db_cliente)	
	
	return {"Result": "Cliente eliminado satisfactoriamente"}
	
@app.put("/actualizar_cliente/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_cliente(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, cliente: schemas.Cliente_UPD, db: Session = Depends(get_db)):
	
	db_cliente = db.query(models.Cliente).filter(models.Cliente.id_cliente == id).first()
	
	if db_cliente is None:
		raise HTTPException(status_code=404, detail="El cliente seleccionado no existen en la base de datos")
		
	db_cliente.cli_genero = cliente.cli_genero
	db_cliente.cli_estado_civil = cliente.cli_estado_civil
	db_cliente.cli_numero_empleos = cliente.cli_numero_empleos
	db_cliente.cli_hijos = cliente.cli_hijos
	db_cliente.cli_pos_tecnica_trabajo = cliente.cli_pos_tecnica_trabajo
	db_cliente.cli_pos_tecnica_hogar = cliente.cli_pos_tecnica_hogar
	db_cliente.cli_cargo = cliente.cli_cargo
	db_cliente.cli_trab_remoto = cliente.cli_trab_remoto
	db_cliente.cli_categoria_docente = cliente.cli_categoria_docente
	db_cliente.cli_categoria_cientifica = cliente.cli_categoria_cientifica
	db_cliente.cli_experiencia_practicas = cliente.cli_experiencia_practicas 
	db_cliente.cli_numero_est_atendidos = cliente.cli_numero_est_atendidos
	
	db.commit()
	db.refresh(db_cliente)	
	return {"Result": "Datos del cliente actualizados satisfactoriamente"}	
	
#############################
###  CONCERTACION TEMA ######
#############################
@app.post("/crear_concertacion_tema/", status_code=status.HTTP_201_CREATED)
async def crear_concertacion_tema(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					concertacion: schemas.Concertacion_Tema, db: Session = Depends(get_db)):
	try:
		db_concertacion = models.Concertacion_Tema(
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
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Cliente")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Cliente")		

@app.get("/leer_concertacion_simple/", status_code=status.HTTP_201_CREATED)  
async def leer_concertacion_simple(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

		db_conc = db.query(models.Concertacion_Tema).all()
		
		return db_conc
		
@app.get("/leer_concertaciones/", status_code=status.HTTP_201_CREATED)  
async def leer_concertaciones(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 

	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.ci.label('prf_ci'),
		models.User.nombre.label('prf_nombre'),
		models.User.primer_appellido.label('prf_primer_appellido'),
		models.User.segundo_appellido.label('prf_segundo_appellido'),
		models.User.email.label('prf_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.ci.label('cli_ci'),
		models.User.nombre.label('cli_nombre'),
		models.User.primer_appellido.label('cli_primer_appellido'),
		models.User.segundo_appellido.label('cli_segundo_appellido'),
		models.User.email.label('cli_email'),	
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las concertaciones				
	db_concertacion = db.query(
			#Datos de Concertacion
			models.Concertacion_Tema.id_conc_tema,
			models.Concertacion_Tema.conc_tema,
			models.Concertacion_Tema.conc_descripcion,
			models.Concertacion_Tema.conc_complejidad,
			models.Concertacion_Tema.conc_valoracion_prof,
			models.Concertacion_Tema.conc_profesor_id,
			models.Concertacion_Tema.conc_actores_externos,
			models.Concertacion_Tema.conc_evaluacion,
			models.Concertacion_Tema.conc_valoracion_cliente,							
			models.Concertacion_Tema.conc_cliente_id,
			models.Concertacion_Tema.conc_activa,
			#Datos de profesor
			models.Profesor.id_profesor,			
			prf_query.c.prf_ci,
			prf_query.c.prf_nombre,
			prf_query.c.prf_primer_appellido,
			prf_query.c.prf_segundo_appellido,
			prf_query.c.prf_email,		
			models.Profesor.prf_entidad_id,
			#Datos de cliente
			models.Cliente.id_cliente,
			cli_query.c.cli_ci,
			cli_query.c.cli_nombre,
			cli_query.c.cli_primer_appellido,
			cli_query.c.cli_segundo_appellido,
			cli_query.c.cli_email,		
			models.Cliente.cli_entidad_id,
			#Datos Entidad Origen
			models.Entidad_Origen.org_siglas,
			models.Entidad_Origen.id_entidad_origen,
			#Datos Entidad Destino
			models.Entidad_Destino.dest_siglas,
			models.Entidad_Destino.id_entidad_destino,
			).select_from(models.Concertacion_Tema
			).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id
			).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
			).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id
			).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id	
			).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
			).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id	
			).all()		
	
	return db_concertacion
	
@app.get("/leer_concertaciones_profesor/{email}", status_code=status.HTTP_201_CREATED)  
async def leer_concertaciones_profesor(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])],
					email: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 

	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.ci.label('prf_ci'),
		models.User.nombre.label('prf_nombre'),
		models.User.primer_appellido.label('prf_primer_appellido'),
		models.User.segundo_appellido.label('prf_segundo_appellido'),
		models.User.email.label('prf_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.ci.label('cli_ci'),
		models.User.nombre.label('cli_nombre'),
		models.User.primer_appellido.label('cli_primer_appellido'),
		models.User.segundo_appellido.label('cli_segundo_appellido'),
		models.User.email.label('cli_email'),	
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las concertaciones				
	db_concertaciones_profesor = db.query(
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema,
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_descripcion,
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_valoracion_prof,
		models.Concertacion_Tema.conc_profesor_id,
		models.Concertacion_Tema.conc_actores_externos,
		models.Concertacion_Tema.conc_evaluacion,
		models.Concertacion_Tema.conc_valoracion_cliente,							
		models.Concertacion_Tema.conc_cliente_id,
		#Datos de profesor
		models.Profesor.id_profesor,			
		prf_query.c.prf_ci,
		prf_query.c.prf_nombre,
		prf_query.c.prf_primer_appellido,
		prf_query.c.prf_segundo_appellido,
		prf_query.c.prf_email,		
		models.Profesor.prf_entidad_id,
		#Datos de cliente
		models.Cliente.id_cliente,
		cli_query.c.cli_ci,
		cli_query.c.cli_nombre,
		cli_query.c.cli_primer_appellido,
		cli_query.c.cli_segundo_appellido,
		cli_query.c.cli_email,		
		models.Cliente.cli_entidad_id,
		#Datos Entidad Origen
		models.Entidad_Origen.org_siglas,
		models.Entidad_Origen.id_entidad_origen,
		#Datos Entidad Destino
		models.Entidad_Destino.dest_siglas,
		models.Entidad_Destino.id_entidad_destino,
		).select_from(models.Concertacion_Tema
		).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id
		).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
		).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id
		).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id	
		).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
		).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id	
		#).where(models.Concertacion_Tema.conc_activa == True
		).where(prf_query.c.prf_email == email
		).all()		
	
	return db_concertaciones_profesor
	
@app.get("/leer_concertaciones_cliente/{email}", status_code=status.HTTP_201_CREATED)  
async def leer_concertaciones_cliente(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					email: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 

	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.ci.label('prf_ci'),
		models.User.nombre.label('prf_nombre'),
		models.User.primer_appellido.label('prf_primer_appellido'),
		models.User.segundo_appellido.label('prf_segundo_appellido'),
		models.User.email.label('prf_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.ci.label('cli_ci'),
		models.User.nombre.label('cli_nombre'),
		models.User.primer_appellido.label('cli_primer_appellido'),
		models.User.segundo_appellido.label('cli_segundo_appellido'),
		models.User.email.label('cli_email'),	
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las concertaciones				
	db_concertaciones_cliente = db.query(
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema,
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_descripcion,
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_valoracion_prof,
		models.Concertacion_Tema.conc_profesor_id,
		models.Concertacion_Tema.conc_actores_externos,
		models.Concertacion_Tema.conc_evaluacion,
		models.Concertacion_Tema.conc_valoracion_cliente,							
		models.Concertacion_Tema.conc_cliente_id,
		#Datos de profesor
		models.Profesor.id_profesor,			
		prf_query.c.prf_ci,
		prf_query.c.prf_nombre,
		prf_query.c.prf_primer_appellido,
		prf_query.c.prf_segundo_appellido,
		prf_query.c.prf_email,		
		models.Profesor.prf_entidad_id,
		#Datos de cliente
		models.Cliente.id_cliente,
		cli_query.c.cli_ci,
		cli_query.c.cli_nombre,
		cli_query.c.cli_primer_appellido,
		cli_query.c.cli_segundo_appellido,
		cli_query.c.cli_email,		
		models.Cliente.cli_entidad_id,
		#Datos Entidad Origen
		models.Entidad_Origen.org_siglas,
		models.Entidad_Origen.id_entidad_origen,
		#Datos Entidad Destino
		models.Entidad_Destino.dest_siglas,
		models.Entidad_Destino.id_entidad_destino,
		).select_from(models.Concertacion_Tema
		).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id
		).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
		).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id
		).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id	
		).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
		).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id	
		#).where(models.Concertacion_Tema.conc_activa == True
		).where(cli_query.c.cli_email == email
		).all()		
	
	return db_concertaciones_cliente
	
@app.delete("/eliminar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_concertacion(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	db_concertacion = db.query(models.Concertacion_Tema
						).filter(models.Concertacion_Tema.id_conc_tema == id
						).first()
	if db_concertacion is None:
		raise HTTPException(status_code=404, detail="La concertacion no existe en la base de datos")	
	db.delete(db_concertacion)	
	db.commit()
	return {"Result": "Concertacion eliminada satisfactoriamente"}
	
@app.put("/evaluar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def evaluar_concertacion(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])], 
				id: str, conc_eva: schemas.Concertacion_Tema_Eval, db: Session = Depends(get_db)):
	
	db_concertacion = db.query(models.Concertacion_Tema).filter(models.Concertacion_Tema.id_conc_tema == id).first()
	
	if db_concertacion is None:
		raise HTTPException(status_code=404, detail="Concertacion no existe ne base de datos")
		
	db_concertacion.conc_evaluacion = conc_eva.conc_evaluacion 	
	
	db.commit()
	db.refresh(db_concertacion)	
	return db_concertacion
	
@app.put("/actualizar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_concertacion(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, concertacion: schemas.Concertacion_Tema_UPD, db: Session = Depends(get_db)):
	
	db_conc = db.query(models.Concertacion_Tema).filter(models.Concertacion_Tema.id_conc_tema == id).first()
	
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
	
@app.put("/actualizar_responsables_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_responsables_concertacion(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])], 
				id: str, concertacion: schemas.Concertacion_Tema_UPD_Actores, db: Session = Depends(get_db)):
	
	db_conc = db.query(models.Concertacion_Tema).filter(models.Concertacion_Tema.id_conc_tema == id).first()
	if db_conc is None:
		raise HTTPException(status_code=404, detail="La concertacion de tema seleccionada no existen en la base de datos")
		
	db_conc.conc_profesor_id = concertacion.conc_profesor_id
	db_conc.conc_cliente_id = concertacion.conc_cliente_id	
	db.commit()
	db.refresh(db_conc)	
	return {"Result": "Datos de responsables de la concertacion de tema actualizados satisfactoriamente"}	
	
@app.put("/activar_concertacion/{id}", status_code=status.HTTP_201_CREATED) 
async def activar_concertacion(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])], 
				id: str, concertacion: schemas.Concertacion_Tema_Activate, db: Session = Depends(get_db)):
	
	db_conc = db.query(models.Concertacion_Tema).filter(models.Concertacion_Tema.id_conc_tema == id).first()
	if db_conc is None:
		raise HTTPException(status_code=404, detail="La concertacion de tema seleccionada no existen en la base de datos")	
	
	db_conc.conc_activa = concertacion.conc_activa
	
	db.commit()
	db.refresh(db_conc)	
	return {"Result": "Cambio de concertacion desarrollada satisfactoriamente"}	
	
#############################
####### TIPO TAREA  #########
#############################
@app.post("/crear_tipo_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_tipo_tarea(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					tarea: schemas.Tipo_Tarea, db: Session = Depends(get_db)):
	try:
		db_tipo_tarea = models.Tipo_Tarea(
			tarea_tipo_nombre = tarea.tarea_tipo_nombre			
		)			
		db.add(db_tipo_tarea)   	
		db.commit()
		db.refresh(db_tipo_tarea)			
		return db_tipo_tarea
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Tipo Tarea")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Tipo Tarea")		

@app.get("/leer_tipos_tareas/", status_code=status.HTTP_201_CREATED)  
async def leer_tipos_tareas(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	db_tipos_tareas = db.query(models.Tipo_Tarea).all()	
	
	return db_tipos_tareas
	
@app.delete("/eliminar_tipo_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_tipo_tarea(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	
	db_tipo_tarea = db.query(models.Tipo_Tarea
						).filter(models.Tipo_Tarea.id_tipo_tarea == id
						).first()
	
	if db_tipo_tarea is None:
		raise HTTPException(status_code=404, detail="El tipo de tarea no existe en la base de datos")	
	
	db.delete(db_tipo_tarea)	
	db.commit()
	return {"Result": "Tarea eliminada satisfactoriamente"}
	
@app.put("/actualizar_tipo_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_tipo_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, tarea: schemas.Tipo_Tarea, db: Session = Depends(get_db)):
	
	db_tipo_tarea = db.query(models.Tipo_Tarea).filter(models.Tipo_Tarea.id_tipo_tarea == id).first()
	
	if db_tipo_tarea is None:
		raise HTTPException(status_code=404, detail="El tipo de tarea seleccionado no existen en la base de datos")
		
	db_tipo_tarea.tarea_tipo_nombre = tarea.tarea_tipo_nombre	
	
	db.commit()
	db.refresh(db_tipo_tarea)	
	return {"Result": "Datos del tipo de tarea actualizados satisfactoriamente"}	
	
#############################
###  ASIGNACION TAREA  ######
#############################
@app.post("/crear_asignacion_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_asignacion_tarea(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					asg_tarea: schemas.Asignacion_Tarea, db: Session = Depends(get_db)):
	try:
		db_asg_tarea = models.Asignacion_Tarea(
			asg_descripcion = asg_tarea.asg_descripcion,
			asg_fecha_inicio = asg_tarea.asg_fecha_inicio, 
			asg_fecha_fin = asg_tarea.asg_fecha_fin, 
			asg_complejidad_estimada = asg_tarea.asg_complejidad_estimada, 
			asg_participantes = asg_tarea.asg_participantes,  #Numero de miembros en el equipo
			asg_tipo_tarea_id = asg_tarea.asg_tipo_tarea_id,
			asg_estudiante_id = asg_tarea.asg_estudiante_id,    
			asg_conc_id = asg_tarea.asg_conc_id,
			asg_evaluacion = "Mejorable"
		)			
		db.add(db_asg_tarea)   	
		db.commit()
		db.refresh(db_asg_tarea)			
		return db_asg_tarea
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Asignacion_Tareas")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Asignacion_Tareas")		

@app.get("/leer_asig_tarea_simple/", status_code=status.HTTP_201_CREATED)  
async def leer_asig_tarea_simple(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

		db_asg = db.query(models.Asignacion_Tarea).all()
		
		return db_asg
		
		
@app.get("/leer_asgignaciones_tareas/", status_code=status.HTTP_201_CREATED)  
async def leer_asgignaciones_tareas(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.ci.label('est_ci'),
		models.User.nombre.label('est_nombre'),
		models.User.primer_appellido.label('est_primer_appellido'),
		models.User.segundo_appellido.label('est_segundo_appellido'),
		models.User.email.label('est_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.ci.label('prf_ci'),
		models.User.nombre.label('prf_nombre'),
		models.User.primer_appellido.label('prf_primer_appellido'),
		models.User.segundo_appellido.label('prf_segundo_appellido'),
		models.User.email.label('prf_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.ci.label('cli_ci'),
		models.User.nombre.label('cli_nombre'),
		models.User.primer_appellido.label('cli_primer_appellido'),
		models.User.segundo_appellido.label('cli_segundo_appellido'),
		models.User.email.label('cli_email'),	
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las asignaciones
	db_asgnaciones_tareas = db.query(
		#Datos de Asignacion
		models.Asignacion_Tarea.id_asignacion,
		models.Asignacion_Tarea.asg_descripcion,
		models.Asignacion_Tarea.asg_fecha_inicio,
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		models.Asignacion_Tarea.asg_evaluacion,
		models.Asignacion_Tarea.asg_tipo_tarea_id,
		models.Asignacion_Tarea.asg_estudiante_id,
		models.Asignacion_Tarea.asg_conc_id,
		models.Asignacion_Tarea.asg_activa,
		#Datos Tipo de tarea
		models.Tipo_Tarea.id_tipo_tarea,
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema,
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_profesor_id,						
		models.Concertacion_Tema.conc_cliente_id,
		#Datos de Estudiante
		models.Estudiante.id_estudiante,
		models.Estudiante.est_entidad_id,
		est_query.c.est_ci,
		est_query.c.est_nombre,
		est_query.c.est_primer_appellido,
		est_query.c.est_segundo_appellido,
		est_query.c.est_email,		
		#Datos de profesor
		models.Profesor.id_profesor,			
		prf_query.c.prf_ci,
		prf_query.c.prf_nombre,
		prf_query.c.prf_primer_appellido,
		prf_query.c.prf_segundo_appellido,
		prf_query.c.prf_email,		
		models.Profesor.prf_entidad_id,
		#Datos de cliente
		models.Cliente.id_cliente,
		cli_query.c.cli_ci,
		cli_query.c.cli_nombre,
		cli_query.c.cli_primer_appellido,
		cli_query.c.cli_segundo_appellido,
		cli_query.c.cli_email,		
		models.Cliente.cli_entidad_id,
		).select_from(models.Asignacion_Tarea
		).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
		).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
		).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id	
		).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id	
		).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Estudiante.est_entidad_id	
		).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id	
		).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
		).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id	
		).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id	
		).all()	
	
	return db_asgnaciones_tareas

@app.get("/leer_asgignacion_estudiante/{email}", status_code=status.HTTP_201_CREATED)  
async def leer_asgignacion_estudiante(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["estudiante"])],
					email: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.ci.label('est_ci'),
		models.User.nombre.label('est_nombre'),
		models.User.primer_appellido.label('est_primer_appellido'),
		models.User.segundo_appellido.label('est_segundo_appellido'),
		models.User.email.label('est_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.ci.label('prf_ci'),
		models.User.nombre.label('prf_nombre'),
		models.User.primer_appellido.label('prf_primer_appellido'),
		models.User.segundo_appellido.label('prf_segundo_appellido'),
		models.User.email.label('prf_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.ci.label('cli_ci'),
		models.User.nombre.label('cli_nombre'),
		models.User.primer_appellido.label('cli_primer_appellido'),
		models.User.segundo_appellido.label('cli_segundo_appellido'),
		models.User.email.label('cli_email'),	
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las asignaciones
	db_asgnacion = db.query(
		#Datos de Asignacion
		models.Asignacion_Tarea.id_asignacion,
		models.Asignacion_Tarea.asg_descripcion,
		models.Asignacion_Tarea.asg_fecha_inicio,
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		models.Asignacion_Tarea.asg_evaluacion,
		models.Asignacion_Tarea.asg_tipo_tarea_id,
		models.Asignacion_Tarea.asg_estudiante_id,
		models.Asignacion_Tarea.asg_conc_id,
		#Datos Tipo de tarea
		models.Tipo_Tarea.id_tipo_tarea,
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema,
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_profesor_id,						
		models.Concertacion_Tema.conc_cliente_id,
		#Datos de Estudiante
		models.Estudiante.id_estudiante,
		models.Estudiante.est_entidad_id,
		est_query.c.est_ci,
		est_query.c.est_nombre,
		est_query.c.est_primer_appellido,
		est_query.c.est_segundo_appellido,
		est_query.c.est_email,		
		#Datos de profesor
		models.Profesor.id_profesor,			
		prf_query.c.prf_ci,
		prf_query.c.prf_nombre,
		prf_query.c.prf_primer_appellido,
		prf_query.c.prf_segundo_appellido,
		prf_query.c.prf_email,		
		models.Profesor.prf_entidad_id,
		#Datos de cliente
		models.Cliente.id_cliente,
		cli_query.c.cli_ci,
		cli_query.c.cli_nombre,
		cli_query.c.cli_primer_appellido,
		cli_query.c.cli_segundo_appellido,
		cli_query.c.cli_email,		
		models.Cliente.cli_entidad_id,
		).select_from(models.Asignacion_Tarea
		).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
		).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
		).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id	
		).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id	
		).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Estudiante.est_entidad_id	
		).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id	
		).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
		).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id	
		).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id	
		).where(models.Asignacion_Tarea.asg_activa == True
		).where(est_query.c.est_email == email
		).first()	
	
	return db_asgnacion
	
@app.get("/leer_profesor_asgignaciones/{email}", status_code=status.HTTP_201_CREATED)  
async def leer_profesor_asgignaciones(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])],
					email: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.ci.label('est_ci'),
		models.User.nombre.label('est_nombre'),
		models.User.primer_appellido.label('est_primer_appellido'),
		models.User.segundo_appellido.label('est_segundo_appellido'),
		models.User.email.label('est_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.ci.label('prf_ci'),
		models.User.nombre.label('prf_nombre'),
		models.User.primer_appellido.label('prf_primer_appellido'),
		models.User.segundo_appellido.label('prf_segundo_appellido'),
		models.User.email.label('prf_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.ci.label('cli_ci'),
		models.User.nombre.label('cli_nombre'),
		models.User.primer_appellido.label('cli_primer_appellido'),
		models.User.segundo_appellido.label('cli_segundo_appellido'),
		models.User.email.label('cli_email'),	
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las asignaciones
	db_profesor_asgnaciones = db.query(
		#Datos de Asignacion
		models.Asignacion_Tarea.id_asignacion,
		models.Asignacion_Tarea.asg_descripcion,
		models.Asignacion_Tarea.asg_fecha_inicio,
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		models.Asignacion_Tarea.asg_evaluacion,
		models.Asignacion_Tarea.asg_tipo_tarea_id,
		models.Asignacion_Tarea.asg_estudiante_id,
		models.Asignacion_Tarea.asg_conc_id,
		#Datos Tipo de tarea
		models.Tipo_Tarea.id_tipo_tarea,
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema,
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_profesor_id,						
		models.Concertacion_Tema.conc_cliente_id,
		#Datos de Estudiante
		models.Estudiante.id_estudiante,
		models.Estudiante.est_entidad_id,
		est_query.c.est_ci,
		est_query.c.est_nombre,
		est_query.c.est_primer_appellido,
		est_query.c.est_segundo_appellido,
		est_query.c.est_email,		
		#Datos de profesor
		models.Profesor.id_profesor,			
		prf_query.c.prf_ci,
		prf_query.c.prf_nombre,
		prf_query.c.prf_primer_appellido,
		prf_query.c.prf_segundo_appellido,
		prf_query.c.prf_email,		
		models.Profesor.prf_entidad_id,
		#Datos de cliente
		models.Cliente.id_cliente,
		cli_query.c.cli_ci,
		cli_query.c.cli_nombre,
		cli_query.c.cli_primer_appellido,
		cli_query.c.cli_segundo_appellido,
		cli_query.c.cli_email,		
		models.Cliente.cli_entidad_id,
		).select_from(models.Asignacion_Tarea
		).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
		).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
		).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id	
		).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id	
		).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Estudiante.est_entidad_id	
		).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id	
		).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
		).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id	
		).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id	
		).where(models.Asignacion_Tarea.asg_activa == True
		).where(prf_query.c.prf_email == email
		).all()	
	
	return db_profesor_asgnaciones
	
@app.get("/leer_cliente_asgignaciones/{email}", status_code=status.HTTP_201_CREATED)  
async def leer_cliente_asgignaciones(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])],
					email: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.ci.label('est_ci'),
		models.User.nombre.label('est_nombre'),
		models.User.primer_appellido.label('est_primer_appellido'),
		models.User.segundo_appellido.label('est_segundo_appellido'),
		models.User.email.label('est_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.ci.label('prf_ci'),
		models.User.nombre.label('prf_nombre'),
		models.User.primer_appellido.label('prf_primer_appellido'),
		models.User.segundo_appellido.label('prf_segundo_appellido'),
		models.User.email.label('prf_email'),	
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.ci.label('cli_ci'),
		models.User.nombre.label('cli_nombre'),
		models.User.primer_appellido.label('cli_primer_appellido'),
		models.User.segundo_appellido.label('cli_segundo_appellido'),
		models.User.email.label('cli_email'),	
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las asignaciones
	db_cliente_asgnaciones = db.query(
		#Datos de Asignacion
		models.Asignacion_Tarea.id_asignacion,
		models.Asignacion_Tarea.asg_descripcion,
		models.Asignacion_Tarea.asg_fecha_inicio,
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		models.Asignacion_Tarea.asg_evaluacion,
		models.Asignacion_Tarea.asg_tipo_tarea_id,
		models.Asignacion_Tarea.asg_estudiante_id,
		models.Asignacion_Tarea.asg_conc_id,
		#Datos Tipo de tarea
		models.Tipo_Tarea.id_tipo_tarea,
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema,
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_profesor_id,						
		models.Concertacion_Tema.conc_cliente_id,
		#Datos de Estudiante
		models.Estudiante.id_estudiante,
		models.Estudiante.est_entidad_id,
		est_query.c.est_ci,
		est_query.c.est_nombre,
		est_query.c.est_primer_appellido,
		est_query.c.est_segundo_appellido,
		est_query.c.est_email,		
		#Datos de profesor
		models.Profesor.id_profesor,			
		prf_query.c.prf_ci,
		prf_query.c.prf_nombre,
		prf_query.c.prf_primer_appellido,
		prf_query.c.prf_segundo_appellido,
		prf_query.c.prf_email,		
		models.Profesor.prf_entidad_id,
		#Datos de cliente
		models.Cliente.id_cliente,
		cli_query.c.cli_ci,
		cli_query.c.cli_nombre,
		cli_query.c.cli_primer_appellido,
		cli_query.c.cli_segundo_appellido,
		cli_query.c.cli_email,		
		models.Cliente.cli_entidad_id,
		).select_from(models.Asignacion_Tarea
		).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
		).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
		).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id	
		).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id	
		).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Estudiante.est_entidad_id	
		).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id	
		).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
		).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id	
		).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id	
		).where(models.Asignacion_Tarea.asg_activa == True
		).where(cli_query.c.cli_email == email
		).all()	
	
	return db_cliente_asgnaciones
	
@app.delete("/eliminar_asgignacion_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_asgignacion_tarea(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					id: str, db: Session = Depends(get_db)):
	db_asg_tarea = db.query(models.Asignacion_Tarea
						).filter(models.Asignacion_Tarea.id_asignacion == id
						).first()
	if db_asg_tarea is None:
		raise HTTPException(status_code=404, detail="La asignacion no existe en la base de datos")	
	db.delete(db_asg_tarea)	
	db.commit()
	return {"Result": "Asignacion de Tarea eliminada satisfactoriamente"}

@app.put("/evaluar_asignacion_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def evaluar_asignacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])], 
				id: str, asg_tarea_eva: schemas.Asignacion_Tarea_Eval, db: Session = Depends(get_db)):
	db_asg_tarea = db.query(models.Asignacion_Tarea).filter(models.Asignacion_Tarea.id_asignacion == id).first()
	if db_asg_tarea is None:
		raise HTTPException(status_code=404, detail="Tarea no existe ne la base de datos")
	db_asg_tarea.asg_evaluacion = asg_tarea_eva.asg_evaluacion 	
	db.commit()
	db.refresh(db_asg_tarea)	
	return db_asg_tarea
	
@app.put("/actualizar_asignacion_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_asignacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, asg_tarea: schemas.Asignacion_Tarea_UPD, db: Session = Depends(get_db)):
	
	db_asg = db.query(models.Asignacion_Tarea).filter(models.Asignacion_Tarea.id_asignacion == id).first()
	
	if db_asg is None:
		raise HTTPException(status_code=404, detail="La asignacion de tareas seleccionada no existen en la base de datos")
		
	db_asg.asg_descripcion = asg_tarea.asg_descripcion
	db_asg.asg_fecha_inicio = asg_tarea.asg_fecha_inicio
	db_asg.asg_fecha_fin = asg_tarea.asg_fecha_fin
	db_asg.asg_complejidad_estimada = asg_tarea.asg_complejidad_estimada
	db_asg.asg_participantes = asg_tarea.asg_participantes
	
	db.commit()
	db.refresh(db_asg)	
	return {"Result": "Datos de la asignacion actualizados satisfactoriamente"}	
	
@app.put("/actualizar_asignacion_tarea_tipo/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_asignacion_tarea_tipo(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, asg_tarea: schemas.Asignacion_Tarea_UPD_Tipo, db: Session = Depends(get_db)):
	
	db_asg = db.query(models.Asignacion_Tarea).filter(models.Asignacion_Tarea.id_asignacion == id).first()
	
	if db_asg is None:
		raise HTTPException(status_code=404, detail="La asignacion de tareas seleccionada no existen en la base de datos")
		
	db_asg.asg_tipo_tarea_id = asg_tarea.asg_tipo_tarea_id
	
	db.commit()
	db.refresh(db_asg)	
	return {"Result": "Datos para el tipo de tarea de la asignacion actualizados satisfactoriamente"}	
	
@app.put("/activar_asignacion_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def activar_asignacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])], 
				id: str, db: Session = Depends(get_db)):
	
	db_asg = db.query(models.Asignacion_Tarea).filter(models.Asignacion_Tarea.id_asignacion == id).first()	
	if db_asg is None:
		raise HTTPException(status_code=404, detail="La asignacion de tareas seleccionada no existen en la base de datos")
		
	if db_asg.asg_activa == True:
		db_asg.asg_activa = False 
	else: 
		db_asg.asg_activa = True 
		
	db.commit()
	db.refresh(db_asg)	
	return {"Result": "Datos para el tipo de tarea de la asignacion actualizados satisfactoriamente"}	
	
#############################
###  ACTIVIDADES TAREA  #####
#############################
@app.post("/crear_actividad_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_actividad_tarea(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					act_tarea: schemas.Actividades_Tarea, db: Session = Depends(get_db)):
	try:
		db_act_tarea = models.Actividades_Tarea(
			act_nombre = act_tarea.act_nombre,
			act_est_memo = act_tarea.act_est_memo,
			act_prof_memo = act_tarea.act_prof_memo,
			act_cli_memo = act_tarea.act_cli_memo,
			act_resultado = "Iniciada",
			id_asg_act = act_tarea.id_asg_act		
		)			
		db.add(db_act_tarea)   	
		db.commit()
		db.refresh(db_act_tarea)			
		return db_act_tarea
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Actividades_Tarea")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Actividades_Tarea")	

@app.post("/crear_actividad_tarea_profesor/{id}", status_code=status.HTTP_201_CREATED)
async def crear_actividad_tarea_profesor(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])],
					id: str, act_tarea: schemas.Actividades_Tarea_Prf, db: Session = Depends(get_db)):
					
	db_asignacion = db.query(models.Asignacion_Tarea).where(models.Asignacion_Tarea.id_asignacion == id).first()
	
	if db_asignacion is None:
		raise HTTPException(status_code=404, detail="La asignacion de tarea seleccionada no existe en la base de datos")
	
	try:
		db_act_tarea = models.Actividades_Tarea(
			act_nombre = act_tarea.act_nombre,
			act_prof_memo = act_tarea.act_prof_memo,
			act_resultado = "Iniciada",
			id_asg_act = db_asignacion.id_asignacion		
		)			
		db.add(db_act_tarea)   	
		db.commit()
		db.refresh(db_act_tarea)			
		return db_act_tarea
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Actividades_Tarea")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Actividades_Tarea")				

@app.get("/leer_actividades_tareas/", status_code=status.HTTP_201_CREATED)  
async def leer_actividades_tareas(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_actividades_tareas = db.query(models.Actividades_Tarea).all()	
	
	return db_actividades_tareas
	
@app.get("/leer_actividades_tareas_asignacion/{id}", status_code=status.HTTP_201_CREATED)  
async def leer_actividades_tareas_asignacion(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["estudiante"])],
					id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
	
	#Datos para predecir las asignaciones
	act_query = db.query(
		models.Actividades_Tarea.act_nombre,
		models.Actividades_Tarea.act_prof_memo,
		models.Actividades_Tarea.act_resultado,
		models.Actividades_Tarea.id_asg_act,
		).select_from(models.Actividades_Tarea
		).where(models.Actividades_Tarea.id_asg_act == id
		).all()	
	
	return act_query
	
@app.get("/leer_tareas_estudiante/{email}", status_code=status.HTTP_201_CREATED)  
async def leer_tareas_estudiante(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["estudiante"])],
					email: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.ci.label('est_ci'),
		models.User.nombre.label('est_nombre'),
		models.User.primer_appellido.label('est_primer_appellido'),
		models.User.segundo_appellido.label('est_segundo_appellido'),
		models.User.email.label('est_email'),
	).select_from(
		models.User
	).subquery()
	
	#Datos para predecir las asignaciones
	db_tareas = db.query(
		#Datos de Estudiante
		models.Estudiante.id_estudiante,
		models.Estudiante.est_entidad_id,
		models.Estudiante.user_estudiante_id,
		est_query.c.est_ci,
		est_query.c.est_nombre,
		est_query.c.est_primer_appellido,
		est_query.c.est_segundo_appellido,
		est_query.c.est_email,			
		#Datos de Asignacion
		models.Asignacion_Tarea.id_asignacion,
		models.Asignacion_Tarea.asg_descripcion,
		models.Asignacion_Tarea.asg_fecha_inicio,
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		models.Asignacion_Tarea.asg_evaluacion,
		models.Asignacion_Tarea.asg_tipo_tarea_id,
		models.Asignacion_Tarea.asg_estudiante_id,
		models.Asignacion_Tarea.asg_conc_id,
		#Actividades tarea
		models.Actividades_Tarea.id_actividad_tarea,
		models.Actividades_Tarea.act_nombre,
		models.Actividades_Tarea.act_resultado,
		models.Actividades_Tarea.act_est_memo,
		models.Actividades_Tarea.act_prof_memo,
		models.Actividades_Tarea.act_cli_memo,
		models.Actividades_Tarea.id_asg_act,
	).select_from(models.Actividades_Tarea
	).join(models.Asignacion_Tarea, models.Asignacion_Tarea.id_asignacion == models.Actividades_Tarea.id_asg_act
	).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id
	).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id		
	).where(est_query.c.est_email == email
	).all()	
	
	return db_tareas
	
@app.get("/leer_tareas_estudiante_por_profesor/{email}", status_code=status.HTTP_201_CREATED)  
async def leer_tareas_estudiante_por_profesor(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])],
					email: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.ci.label('est_ci'),
		models.User.nombre.label('est_nombre'),
		models.User.primer_appellido.label('est_primer_appellido'),
		models.User.segundo_appellido.label('est_segundo_appellido'),
		models.User.email.label('est_email'),
	).select_from(
		models.User
	).subquery()
	
	#Datos para predecir las asignaciones
	db_tareas = db.query(
		#Datos de Estudiante
		models.Estudiante.id_estudiante,
		models.Estudiante.est_entidad_id,
		models.Estudiante.user_estudiante_id,
		est_query.c.est_ci,
		est_query.c.est_nombre,
		est_query.c.est_primer_appellido,
		est_query.c.est_segundo_appellido,
		est_query.c.est_email,			
		#Datos de Asignacion
		models.Asignacion_Tarea.id_asignacion,
		models.Asignacion_Tarea.asg_descripcion,
		models.Asignacion_Tarea.asg_fecha_inicio,
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		models.Asignacion_Tarea.asg_evaluacion,
		models.Asignacion_Tarea.asg_tipo_tarea_id,
		models.Asignacion_Tarea.asg_estudiante_id,
		models.Asignacion_Tarea.asg_conc_id,
		#Actividades tarea
		models.Actividades_Tarea.id_actividad_tarea,
		models.Actividades_Tarea.act_nombre,
		models.Actividades_Tarea.act_resultado,
		models.Actividades_Tarea.act_est_memo,
		models.Actividades_Tarea.act_prof_memo,
		models.Actividades_Tarea.act_cli_memo,
		models.Actividades_Tarea.id_asg_act,
	).select_from(models.Actividades_Tarea
	).join(models.Asignacion_Tarea, models.Asignacion_Tarea.id_asignacion == models.Actividades_Tarea.id_asg_act
	).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id
	).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id		
	).where(est_query.c.est_email == email
	).all()	
	
	return db_tareas
	
@app.delete("/eliminar_actividad_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_actividad_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])],
					id: str, db: Session = Depends(get_db)):
	db_act_tarea = db.query(models.Actividades_Tarea
						).filter(models.Actividades_Tarea.id_actividad_tarea == id
						).first()
	if db_act_tarea is None:
		raise HTTPException(status_code=404, detail="La actividad no existe en la base de datos")	
	db.delete(db_act_tarea)	
	db.commit()
	return {"Result": "Actividad de Tarea eliminada satisfactoriamente"}
	
@app.put("/evaluar_actividad_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def evaluar_actividad_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])], 
				id: str, act_tarea_res: schemas.Actividades_Tarea_Eval, db: Session = Depends(get_db)):
	db_act_tarea = db.query(models.Actividades_Tarea).filter(models.Actividades_Tarea.id_actividad_tarea == id).first()
	if db_act_tarea is None:
		raise HTTPException(status_code=404, detail="Actividad Tarea no existe ne la base de datos")
	db_act_tarea.act_resultado = act_tarea_res.act_resultado 	
	db.commit()
	db.refresh(db_act_tarea)	
	return db_act_tarea
	
@app.put("/actualizar_actividad_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_actividad_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor", "cliente"])], 
				id: str, act_tarea: schemas.Actividades_Tarea, db: Session = Depends(get_db)):
	db_act = db.query(models.Actividades_Tarea).filter(models.Actividades_Tarea.id_actividad_tarea == id).first()
	if db_act is None:
		raise HTTPException(status_code=404, detail="La actividad seleccionada no existen en la base de datos")
		
	db_act.act_nombre = act_tarea.act_nombre	
	
	db.commit()
	db.refresh(db_act)	
	return {"Result": "Datos del nombre de la actividad actualizados satisfactoriamente"}	
	
@app.put("/actualizar_actividad_tarea_estudiante/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_actividad_tarea_estudiante(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["estudiante"])], 
				id: str, act_tarea: schemas.Actividades_Tarea_UPD_Est, db: Session = Depends(get_db)):
	db_act = db.query(models.Actividades_Tarea).filter(models.Actividades_Tarea.id_actividad_tarea == id).first()
	if db_act is None:
		raise HTTPException(status_code=404, detail="La actividad seleccionada no existen en la base de datos")
		
	db_act.act_est_memo = act_tarea.act_est_memo	
	
	db.commit()
	db.refresh(db_act)	
	return {"Result": "Datos de la opinion del estudiante de la actividad actualizados satisfactoriamente"}	
	
@app.put("/actualizar_actividad_tarea_profesor/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_actividad_tarea_profesor(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["profesor"])], 
				id: str, act_tarea: schemas.Actividades_Tarea_UPD_Prf, db: Session = Depends(get_db)):
	db_act = db.query(models.Actividades_Tarea).filter(models.Actividades_Tarea.id_actividad_tarea == id).first()
	if db_act is None:
		raise HTTPException(status_code=404, detail="La actividad seleccionada no existen en la base de datos")
		
	db_act.act_prof_memo = act_tarea.act_prof_memo	
	
	db.commit()
	db.refresh(db_act)	
	return {"Result": "Datos de la opinion del profesor de la actividad actualizados satisfactoriamente"}	
	
@app.put("/actualizar_actividad_tarea_cliente/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_actividad_tarea_cliente(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["cliente"])], 
				id: str, act_tarea: schemas.Actividades_Tarea_UPD_Cli, db: Session = Depends(get_db)):
	db_act = db.query(models.Actividades_Tarea).filter(models.Actividades_Tarea.id_actividad_tarea == id).first()
	if db_act is None:
		raise HTTPException(status_code=404, detail="La actividad seleccionada no existen en la base de datos")
		
	db_act.act_cli_memo = act_tarea.act_cli_memo	
	
	db.commit()
	db.refresh(db_act)	
	return {"Result": "Datos de la opinion del cliente de la actividad actualizados satisfactoriamente"}	
	

##############################################
###  ACTUALIZACION de ASIGNACION DE TAREA  ###
##############################################
@app.post("/crear_actualizacion_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_actualizacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=[ "profesor", "cliente", "estudiante"])],
					act_tarea: schemas.Tareas_Actualizacion, db: Session = Depends(get_db)):
	try:
		db_act_tarea = models.Tareas_Actualizacion(
			memo_actualizacion = act_tarea.memo_actualizacion, 
			id_asg_upd = act_tarea.id_asg_upd,
			fecha_actualizacion = func.now(),			
		)			
		db.add(db_act_tarea)   	
		db.commit()
		db.refresh(db_act_tarea)			
		return db_act_tarea
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Tareas_Actualizacion")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Tareas_Actualizacion")	

@app.get("/leer_actualizaciones_tareas/", status_code=status.HTTP_201_CREATED)  
async def leer_actualizaciones_tareas(current_user: Annotated[schemas.User, Security(get_current_user, scopes=[ "profesor", "cliente", "estudiante"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_actualizaciones_tareas = db.query(models.Tareas_Actualizacion).all()	
	
	return db_actualizaciones_tareas
	
@app.delete("/eliminar_actualizacion_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_actualizacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=[ "profesor", "cliente", "estudiante"])],
					id: str, db: Session = Depends(get_db)):
	db_act_tarea = db.query(models.Tareas_Actualizacion
						).filter(models.Tareas_Actualizacion.id_tareas_act == id
						).first()
	if db_act_tarea is None:
		raise HTTPException(status_code=404, detail="La actividad no existe en la base de datos")	
	db.delete(db_act_tarea)	
	db.commit()
	return {"Result": "Actualizacion de asignacion de Tarea eliminada satisfactoriamente"}
	
@app.put("/actualizar_actualizacion_tarea/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_actualizacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=[ "profesor", "cliente", "estudiante"])], 
				id: str, actualizacion: schemas.Tareas_Actualizacion_UPD, db: Session = Depends(get_db)):
	db_actl = db.query(models.Tareas_Actualizacion).filter(models.Tareas_Actualizacion.id_tareas_act == id).first()
	if db_actl is None:
		raise HTTPException(status_code=404, detail="La actualizacion de tarea seleccionada no existen en la base de datos")
		
	db_actl.fecha_actualizacion = func.now()
	db_actl.memo_actualizacion = actualizacion.memo_actualizacion
	
	db.commit()
	db.refresh(db_actl)	
	return {"Result": "Datos de la actualizacion de asignacion de tarea actualizados satisfactoriamente"}	
	
#############################
###  Gestion al PROFESOR  ###
#############################	
@app.get("/obtener_profesor/{id}", status_code=status.HTTP_201_CREATED) 
async def obtener_profesor(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["admin", "profesor"])], 
				id: str, profesor: schemas.Profesor, db: Session = Depends(get_db)):
				
	db_profesor = db.query(
			#Datos Profesor
			models.Profesor.id_profesor,
			models.Profesor.prf_genero,
			models.Profesor.prf_estado_civil,
			models.Profesor.prf_numero_empleos,
			models.Profesor.prf_hijos,
			models.Profesor.prf_pos_tecnica_trabajo,
			models.Profesor.prf_pos_tecnica_hogar,
			models.Profesor.prf_cargo,
			models.Profesor.prf_trab_remoto,
			models.Profesor.prf_categoria_docente,
			models.Profesor.prf_categoria_cientifica,
			models.Profesor.prf_experiencia_practicas,
			models.Profesor.prf_numero_est_atendidos,
			models.Profesor.prf_entidad_id.label('profesor_entidad'),
			#Datos Entidad Origen
			models.Entidad_Origen.org_siglas,
			models.Entidad_Origen.id_entidad_origen,
			#Datos del usiario
			models.User.ci,
			models.User.nombre,
			models.User.primer_appellido,
			models.User.segundo_appellido,
			models.User.email,							
	).select_from(models.Profesor
	).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
	).join(models.User, models.User.id == models.Profesor.user_profesor_id
	).where(models.Profesor.user_profesor_id == str
	).first()		

	return db_profesor
	
@app.get("/obtener_profesor_concertaciones/{ci}", status_code=status.HTTP_201_CREATED) 
async def obtener_profesor_concertaciones(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["admin", "profesor"])], 
				id: str, profesor: schemas.Profesor, db: Session = Depends(get_db)):
				
	db_profesor = db.query(models.Profesor).filter(models.Profesor.prf_ci == ci).first()	
	if db_profesor is None:
		raise HTTPException(status_code=404, detail="El profesor seleccionado no existen en la base de datos")
	
	db_prof_concertaciones = db.query(
				#Datos de Concertacion
				models.Concertacion_Tema.id_conc_tema.label('id_concertacion'),
				models.Concertacion_Tema.conc_tema,
				models.Concertacion_Tema.conc_descripcion,
				models.Concertacion_Tema.conc_complejidad,
				models.Concertacion_Tema.conc_valoracion_prof,
				models.Concertacion_Tema.conc_actores_externos,
				models.Concertacion_Tema.conc_evaluacion,
				models.Concertacion_Tema.conc_valoracion_cliente,							
				models.Concertacion_Tema.conc_cliente_id,	
				#Datos Cliente
				models.Cliente.id_cliente,								
				models.Cliente.cli_entidad_id.label('cliente_entidad'),
				#Datos Entidad Destino
				models.Entidad_Destino.dest_siglas,
				models.Entidad_Destino.id_entidad_destino,
				#Datos del usiario
				models.User.ci,
				models.User.nombre,
				models.User.primer_appellido,
				models.User.segundo_appellido,
				models.User.email,				
			).select_from(models.Concertacion_Tema
			).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id
			).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.prf_entidad_id
			).join(models.User, models.User.id == models.Cliente.user_cliente_id
			).filter_by(conc_profesor_id = db_profesor.id_profesor
			).all()	
	
	return db_prof_concertaciones 
	

#############################
###  CONSULTAS A LA BD    ###
#############################
@app.get("/obtener_registros_concertaciones/")  
async def obtener_registros_concertaciones(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):  
	
	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.nombre.label('prf_nombre'),
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.nombre.label('cli_nombre'),
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las concertaciones				
	db_concertaciones = db.query(
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema.label('id_concertacion'),
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_descripcion,
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_valoracion_prof,
		models.Concertacion_Tema.conc_profesor_id,
		models.Concertacion_Tema.conc_actores_externos,
		models.Concertacion_Tema.conc_evaluacion,
		models.Concertacion_Tema.conc_valoracion_cliente,							
		models.Concertacion_Tema.conc_cliente_id,
		#Datos de profesor
		models.Profesor.id_profesor,
		prf_query.c.prf_nombre,
		models.Profesor.prf_genero,
		models.Profesor.prf_estado_civil,
		models.Profesor.prf_numero_empleos,
		models.Profesor.prf_hijos,
		models.Profesor.prf_cargo,
		models.Profesor.prf_categoria_docente,
		models.Profesor.prf_categoria_cientifica,
		models.Profesor.prf_experiencia_practicas,
		models.Profesor.prf_numero_est_atendidos,
		models.Profesor.prf_trab_remoto,
		#Datos de cliente
		models.Cliente.id_cliente,
		cli_query.c.cli_nombre,
		models.Cliente.cli_genero,
		models.Cliente.cli_estado_civil,
		models.Cliente.cli_numero_empleos,
		models.Cliente.cli_hijos,
		models.Cliente.cli_cargo,
		models.Cliente.cli_categoria_docente,
		models.Cliente.cli_categoria_cientifica,
		models.Cliente.cli_experiencia_practicas,
		models.Cliente.cli_numero_est_atendidos,
		models.Cliente.cli_trab_remoto,
		#Datos Entidad Origen
		models.Entidad_Origen.org_siglas,
		models.Entidad_Origen.id_entidad_origen,
		models.Entidad_Origen.org_transporte,
		models.Entidad_Origen.org_trab_remoto,
		#Datos Entidad Destino
		models.Entidad_Destino.dest_siglas,
		models.Entidad_Destino.id_entidad_destino,
		models.Entidad_Destino.dest_transporte,
		models.Entidad_Destino.dest_experiencia,
		models.Entidad_Destino.dest_trab_remoto,
		).select_from(models.Concertacion_Tema
		).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id
		).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
		).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id	
		).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id			
		).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
		).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id							
		).all()	
	
	return db_concertaciones 
	
@app.get("/obtener_registros_asignaciones/")  
async def obtener_registros_asignaciones(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):  
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.nombre.label('est_nombre'),
	).select_from(
		models.User
	).subquery()
	
	#Datos para predecir las asignaciones
	db_asignaciones = db.query(
		#Datos de Asignacion
		models.Asignacion_Tarea.id_asignacion,
		models.Asignacion_Tarea.asg_descripcion,
		models.Asignacion_Tarea.asg_fecha_inicio,
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		models.Asignacion_Tarea.asg_evaluacion,
		models.Asignacion_Tarea.asg_tipo_tarea_id,
		models.Asignacion_Tarea.asg_estudiante_id,
		models.Asignacion_Tarea.asg_conc_id,
		models.Asignacion_Tarea.asg_evaluacion,
		#Datos Tipo de tarea
		models.Tipo_Tarea.id_tipo_tarea,
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema.label('id_concertacion'),
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_descripcion,
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_valoracion_prof,
		models.Concertacion_Tema.conc_profesor_id,
		models.Concertacion_Tema.conc_valoracion_cliente,							
		models.Concertacion_Tema.conc_cliente_id,
		models.Concertacion_Tema.conc_actores_externos,
		models.Concertacion_Tema.conc_evaluacion,
		#Datos de Estudiante
		models.Estudiante.id_estudiante,
		est_query.c.est_nombre,
		models.Estudiante.est_genero,  
		models.Estudiante.est_estado_civil,
		models.Estudiante.est_trabajo,
		models.Estudiante.est_becado,  
		models.Estudiante.est_hijos, 
		models.Estudiante.est_posibilidad_economica,
		models.Estudiante.est_entidad_id,
		models.Estudiante.est_trab_remoto,
		).select_from(models.Asignacion_Tarea
		).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
		).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
		).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id												
		).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id		
		).all()	
	
	return db_asignaciones 

@app.get("/obtener_registros_actividades/")  
async def obtener_registros_actividades(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):  
	
	#Datos para predecir las actividades basandose en su opinion	
	db_actividades = db.query(							
		models.Actividades_Tarea.id_actividad_tarea,
		models.Actividades_Tarea.act_nombre,
		models.Actividades_Tarea.act_resultado, 
		models.Actividades_Tarea.act_est_memo,
		models.Actividades_Tarea.act_prof_memo,
		models.Actividades_Tarea.act_cli_memo,
		models.Actividades_Tarea.id_asg_act,
		models.Actividades_Tarea.act_resultado,
		).select_from(models.Actividades_Tarea							
		).all()	
	
	return db_actividades 
	
@app.get("/obtener_registros_actividades_asignacion/")  
async def obtener_registros_actividades_asignacion(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):  
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.nombre.label('est_nombre'),
	).select_from(
		models.User
	).subquery()
	
	#Datos para predecir las actividades de tareas			
	db_actividades_asig = db.query(							
		models.Actividades_Tarea.id_actividad_tarea,
		models.Actividades_Tarea.act_nombre,
		models.Actividades_Tarea.act_resultado, 
		models.Actividades_Tarea.act_est_memo,
		models.Actividades_Tarea.act_prof_memo,
		models.Actividades_Tarea.act_cli_memo,
		models.Actividades_Tarea.id_asg_act,
		models.Actividades_Tarea.act_resultado,
		#Datos de Asignacion
		models.Asignacion_Tarea.id_asignacion,
		models.Asignacion_Tarea.asg_descripcion,
		models.Asignacion_Tarea.asg_fecha_inicio,
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		models.Asignacion_Tarea.asg_evaluacion,
		models.Asignacion_Tarea.asg_tipo_tarea_id,
		models.Asignacion_Tarea.asg_estudiante_id,
		models.Asignacion_Tarea.asg_conc_id,
		#Datos Tipo de tarea
		models.Tipo_Tarea.id_tipo_tarea,
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.id_conc_tema.label('id_concertacion'),
		models.Concertacion_Tema.conc_tema,
		models.Concertacion_Tema.conc_descripcion,
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_valoracion_prof,
		models.Concertacion_Tema.conc_profesor_id,
		models.Concertacion_Tema.conc_valoracion_cliente,							
		models.Concertacion_Tema.conc_cliente_id,
		models.Concertacion_Tema.conc_actores_externos,
		models.Concertacion_Tema.conc_evaluacion,
		#Datos de Estudiante
		models.Estudiante.id_estudiante,
		est_query.c.est_nombre,
		models.Estudiante.est_genero,  
		models.Estudiante.est_estado_civil,
		models.Estudiante.est_trabajo,
		models.Estudiante.est_becado,  
		models.Estudiante.est_hijos, 
		models.Estudiante.est_posibilidad_economica,
		models.Estudiante.est_entidad_id,
		models.Estudiante.est_trab_remoto,
		).select_from(models.Actividades_Tarea		
		).join(models.Asignacion_Tarea, models.Asignacion_Tarea.id_asignacion == models.Actividades_Tarea.id_asg_act
		).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
		).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
		).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id
		).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id		
		).all()	
	
	return db_actividades_asig 
	
#############################
#######    HACER CSV    ######
#############################
def create_csv(query, columns_names):
	csvtemp = ""		
	header = [i for i in columns_names]
	csvtemp = ",".join(header) + "\n"
	
	for row in query:		
		csvtemp += (str(row)).replace("(", "").replace(")", "").replace("'", "") + "\n"		
		
	return StringIO(csvtemp)
	
@app.get("/csv_registros_concertaciones/")  
async def csv_registros_concertaciones(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					db: Session = Depends(get_db)):  	
	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.nombre.label('prf_nombre'),
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.nombre.label('cli_nombre'),
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las concertaciones				
	db_concertaciones = db.query(
		#Datos de Concertacion
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_actores_externos,
		#Datos de profesor
		models.Profesor.prf_genero,
		models.Profesor.prf_estado_civil,
		models.Profesor.prf_numero_empleos,
		models.Profesor.prf_hijos,
		models.Profesor.prf_cargo,
		models.Profesor.prf_categoria_docente,
		models.Profesor.prf_categoria_cientifica,
		models.Profesor.prf_experiencia_practicas,
		models.Profesor.prf_numero_est_atendidos,
		models.Profesor.prf_trab_remoto,
		#Datos de cliente
		models.Cliente.cli_genero,
		models.Cliente.cli_estado_civil,
		models.Cliente.cli_numero_empleos,
		models.Cliente.cli_hijos,
		models.Cliente.cli_cargo,
		models.Cliente.cli_categoria_docente,
		models.Cliente.cli_categoria_cientifica,
		models.Cliente.cli_experiencia_practicas,
		models.Cliente.cli_numero_est_atendidos,
		models.Cliente.cli_trab_remoto,
		#Datos Entidad Origen
		models.Entidad_Origen.org_transporte,
		models.Entidad_Origen.org_trab_remoto,
		#Datos Entidad Destino
		models.Entidad_Destino.dest_transporte,
		models.Entidad_Destino.dest_experiencia,
		models.Entidad_Destino.dest_trab_remoto,
		#Evaluacion
		models.Concertacion_Tema.conc_evaluacion,
		).select_from(models.Concertacion_Tema
		).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id
		).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
		).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id	
		).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id			
		).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
		).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id							
		).all()	
					
	columns_conc = ["conc_complejidad","conc_actores_externos"]
	columns_prf = ["prf_genero","prf_estado_civil","prf_numero_empleos","prf_hijos","prf_cargo","prf_categoria_docente","prf_categoria_cientifica","prf_experiencia_practicas","prf_numero_est_atendidos","prf_trab_remoto"]
	columns_cli = ["cli_genero","cli_estado_civil","cli_numero_empleos","cli_hijos","cli_cargo","cli_categoria_docente","cli_categoria_cientifica","cli_experiencia_practicas","cli_numero_est_atendidos","cli_trab_remoto"]
	columns_org = ["org_transporte","org_trab_remoto"]
	columns_des = ["dest_transporte","dest_experiencia","dest_trab_remoto"]
	columns_eval=["conc_evaluacion"]
	columns = columns_conc + columns_prf + columns_cli + columns_org + columns_des + columns_eval
	
	myfile = create_csv(db_concertaciones, columns)	
	headers = {'Content-Disposition': 'attachment; filename="concertaciones.csv"'} 
	return StreamingResponse(iter([myfile.getvalue()]), media_type="application/csv", headers=headers)		  
	
@app.get("/csv_registros_asignaciones/")  
async def csv_registros_asignaciones(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					db: Session = Depends(get_db)):  	
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.nombre.label('est_nombre'),
	).select_from(
		models.User
	).subquery()
	
	#Datos para predecir las asignaciones
	db_asignaciones = db.query(
		#Datos de Asignacion
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,		
		#Datos Tipo de tarea
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_actores_externos,		
		#Datos de Estudiante
		models.Estudiante.est_genero,  
		models.Estudiante.est_estado_civil,
		models.Estudiante.est_trabajo,
		models.Estudiante.est_becado,  
		models.Estudiante.est_hijos, 
		models.Estudiante.est_posibilidad_economica,
		models.Estudiante.est_trab_remoto,
		#Evaluacion
		models.Asignacion_Tarea.asg_evaluacion,
		).select_from(models.Asignacion_Tarea
		).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
		).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
		).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id												
		).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id		
		).all()		
	
	columns_asg=["asg_complejidad_estimada","asg_participantes"]
	columns_tipo=["tarea_tipo_nombre"]
	columns_conc=["conc_complejidad","conc_actores_externos"]
	columns_est=["est_genero","est_estado_civil","est_trabajo","est_becado","est_hijos"," est_posibilidad_economica","est_trab_remoto"]
	columns_eval=["asg_evaluacion"]
	columns = columns_asg + columns_tipo + columns_conc + columns_est + columns_eval
	
	myfile = create_csv(db_asignaciones, columns)	
	headers = {'Content-Disposition': 'attachment; filename="asignaciones.csv"'} 
	return StreamingResponse(iter([myfile.getvalue()]), media_type="application/csv", headers=headers)	

#############################
##### ENTRENAR MODELOS ######
#############################
@app.get("/entrenar_modelo_concertacion/")
async def entrenar_modelo_concertacion(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					db: Session = Depends(get_db)):
					
	#leer datos desde csv
	datos = pd.read_csv("concertaciones.csv", encoding="utf-8")
	#Crear DataFrame
	#Si lo tenemos que leer desde una consulta SQL
	#Particionar los datos
	X = datos.drop(["conc_evaluacion"],axis=1)
	y = datos.conc_evaluacion.values	
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=125)
	
	#Transform data
	# Transformar los datos numericos
	numerical_transformer = Pipeline(steps=[
		('imputer', SimpleImputer(strategy='mean')),
		('scaler', MinMaxScaler())
	])
	# Transformar los datos categoricos
	categorical_transformer = Pipeline(steps=[
		('imputer', SimpleImputer(strategy='most_frequent')),
		('encoder', OrdinalEncoder())
	])
	#Crear la PipeLine
	# Combinar las pipelines de preprocesado de datos usando ColumnTransformer
	preproc_pipe = ColumnTransformer(
		transformers=[
			('num', numerical_transformer, make_column_selector(dtype_include=np.number)),
			('cat', categorical_transformer, make_column_selector(dtype_include=object))
		], remainder="passthrough"
	)	
	#Crear modelo RandomForest Classifier
	rf_model = RandomForestClassifier(n_estimators=100, random_state=125)
	#Crear pipeline de preprocesado de datos y prediccion
	rf_pipe = Pipeline(
		steps=[		   
			("preprocessor", preproc_pipe),
			("rf", rf_model),
		]
	)
	#Entrenar pipeline modelo
	rf_pipe.fit(X_train,y_train)
	# model accuracy
	#predictions = rf_pipe.predict(X_test)
	#Salvar modelo
	joblib.dump(rf_pipe, 'conc_rf_model.pkl')
	 
	return {"Result":"Done"}
	
@app.get("/entrenar_modelo_asignacion_tarea/")
async def entrenar_modelo_asignacion_tarea(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					db: Session = Depends(get_db)):
					
	#leer datos desde csv
	datos = pd.read_csv("asignaciones.csv", encoding="utf-8")
	#Crear DataFrame
	#Si lo tenemos que leer desde una consulta SQL
	#Particionar los datos
	X = datos.drop(["asg_evaluacion"],axis=1)
	y = datos.asg_evaluacion.values	
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=125)
	
	#Transform data 
	# Transformar los datos numericos
	numerical_transformer = Pipeline(steps=[
		('imputer', SimpleImputer(strategy='mean')),
		('scaler', MinMaxScaler())
	])
	# Transformar los datos categoricos
	categorical_transformer = Pipeline(steps=[
		('imputer', SimpleImputer(strategy='most_frequent')),
		('encoder', OrdinalEncoder())
	])
	#Crear la PipeLine
	# Combinar las pipelines de preprocesado de datos usando ColumnTransformer
	preproc_pipe = ColumnTransformer(
		transformers=[
			('num', numerical_transformer, make_column_selector(dtype_include=np.number)),
			('cat', categorical_transformer, make_column_selector(dtype_include=object))
		], remainder="passthrough"
	)	
	#Crear modelo RandomForest Classifier
	rf_model = RandomForestClassifier(n_estimators=100, random_state=125)
	#Crear pipeline de preprocesado de datos y prediccion
	rf_pipe = Pipeline(
		steps=[		   
			("preprocessor", preproc_pipe),
			("rf", rf_model),
		]
	)
	#Entrenar pipeline modelo
	rf_pipe.fit(X_train,y_train)
	# model accuracy
	#predictions = rf_pipe.predict(X_test)
	#Salvar modelo
	joblib.dump(rf_pipe, 'asg_rf_model.pkl')
	 
	return {"Result":"Done"}

#############################
#######  PREDICCIONES  ######
#############################
	
@app.get("/predecir_concertacion/{id}")
async def predecir_concertacion(current_user: Annotated[schemas.User, Depends(get_current_user)],
					id: str, db: Session = Depends(get_db)):
	
	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.nombre.label('prf_nombre'),
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.nombre.label('cli_nombre'),
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las concertaciones				
	db_concertacio = db.query(
		#Datos de Concertacion
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_actores_externos,
		#Datos de profesor
		models.Profesor.prf_genero,
		models.Profesor.prf_estado_civil,
		models.Profesor.prf_numero_empleos,
		models.Profesor.prf_hijos,
		models.Profesor.prf_cargo,
		models.Profesor.prf_categoria_docente,
		models.Profesor.prf_categoria_cientifica,
		models.Profesor.prf_experiencia_practicas,
		models.Profesor.prf_numero_est_atendidos,
		models.Profesor.prf_trab_remoto,
		#Datos de cliente
		models.Cliente.cli_genero,
		models.Cliente.cli_estado_civil,
		models.Cliente.cli_numero_empleos,
		models.Cliente.cli_hijos,
		models.Cliente.cli_cargo,
		models.Cliente.cli_categoria_docente,
		models.Cliente.cli_categoria_cientifica,
		models.Cliente.cli_experiencia_practicas,
		models.Cliente.cli_numero_est_atendidos,
		models.Cliente.cli_trab_remoto,
		#Datos Entidad Origen
		models.Entidad_Origen.org_transporte,
		models.Entidad_Origen.org_trab_remoto,
		#Datos Entidad Destino
		models.Entidad_Destino.dest_transporte,
		models.Entidad_Destino.dest_experiencia,
		models.Entidad_Destino.dest_trab_remoto,
	).select_from(models.Concertacion_Tema
	).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id
	).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
	).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id	
	).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id			
	).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
	).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id	
	).where(models.Concertacion_Tema.id_conc_tema == id  
	).statement
					
	#Preparando datos
	datos = pd.read_sql(db_concertacio, con=engine)	
	#Leer modelo
	loaded_modelo = joblib.load('conc_rf_model.pkl')
	
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
	
@app.get("/predecir_asignacion/{id}")
async def predecir_asignacion(current_user: Annotated[schemas.User, Depends(get_current_user)],
					id: str, db: Session = Depends(get_db)):
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.nombre.label('est_nombre'),
	).select_from(
		models.User
	).subquery()
	
	#Datos para predecir las actividades de tareas			
	db_actividades_asig = db.query(							
		#Datos de Asignacion
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		#Datos Tipo de tarea
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_actores_externos,
		#Datos de Estudiante
		models.Estudiante.est_genero,  
		models.Estudiante.est_estado_civil,
		models.Estudiante.est_trabajo,
		models.Estudiante.est_becado,  
		models.Estudiante.est_hijos, 
		models.Estudiante.est_posibilidad_economica,
		models.Estudiante.est_trab_remoto,
	).select_from(models.Asignacion_Tarea		
	).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
	).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
	).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id
	).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id	
	).where(models.Asignacion_Tarea.id_asignacion == id
	).statement
				
	#Preparando datos
	datos = pd.read_sql(db_actividades_asig, con=engine)
	print(datos.head())
	#Leer modelo
	loaded_modelo = joblib.load('asg_rf_model.pkl')
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
	
	
#############################
#######  ESTADISTICAS  ######
#############################	
@app.get("/estadisticas_general_concertaciones/")
async def estadisticas_general_concertaciones(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					db: Session = Depends(get_db)):
	
	#Datos Profesor
	prf_query = db.query(
		models.User.id.label('prf_user_id'),
		models.User.nombre.label('prf_nombre'),
	).select_from(
		models.User
	).subquery()
	
	#Datos Cliente
	cli_query = db.query(
		models.User.id.label('cli_user_id'),
		models.User.nombre.label('cli_nombre'),
	).select_from(
		models.User
	).subquery()	
	
	#Datos para predecir las concertaciones				
	db_concertaciones = db.query(
		#Datos de Concertacion
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_actores_externos,
		#Datos de profesor
		models.Profesor.prf_genero,
		models.Profesor.prf_estado_civil,
		models.Profesor.prf_numero_empleos,
		models.Profesor.prf_hijos,
		models.Profesor.prf_cargo,
		models.Profesor.prf_categoria_docente,
		models.Profesor.prf_categoria_cientifica,
		models.Profesor.prf_experiencia_practicas,
		models.Profesor.prf_numero_est_atendidos,
		models.Profesor.prf_trab_remoto,
		#Datos de cliente
		models.Cliente.cli_genero,
		models.Cliente.cli_estado_civil,
		models.Cliente.cli_numero_empleos,
		models.Cliente.cli_hijos,
		models.Cliente.cli_cargo,
		models.Cliente.cli_categoria_docente,
		models.Cliente.cli_categoria_cientifica,
		models.Cliente.cli_experiencia_practicas,
		models.Cliente.cli_numero_est_atendidos,
		models.Cliente.cli_trab_remoto,
		#Datos Entidad Origen
		models.Entidad_Origen.org_transporte,
		models.Entidad_Origen.org_trab_remoto,
		#Datos Entidad Destino
		models.Entidad_Destino.dest_transporte,
		models.Entidad_Destino.dest_experiencia,
		models.Entidad_Destino.dest_trab_remoto,
	).select_from(models.Concertacion_Tema
	).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id
	).join(prf_query, prf_query.c.prf_user_id == models.Profesor.user_profesor_id	
	).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id	
	).join(cli_query, cli_query.c.cli_user_id == models.Cliente.user_cliente_id			
	).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
	).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id							
	).statement
					   
	datos = pd.read_sql(db_concertaciones, con=engine)	
	#Preparando datos
	print(datos.describe())
	
						
	return {"Return":"Res"}
	
@app.get("/estadisticas_actividades_asignacion/")
async def estadisticas_actividades_asignacion(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
					db: Session = Depends(get_db)):
	
	#Datos Estudiante
	est_query = db.query(
		models.User.id.label('est_user_id'),
		models.User.nombre.label('est_nombre'),
	).select_from(
		models.User
	).subquery()
	
	#Datos para predecir las actividades de tareas			
	db_actividades_asig = db.query(							
		#Datos de Asignacion
		models.Asignacion_Tarea.asg_complejidad_estimada,
		models.Asignacion_Tarea.asg_participantes,
		#Datos Tipo de tarea
		models.Tipo_Tarea.tarea_tipo_nombre,
		#Datos de Concertacion
		models.Concertacion_Tema.conc_complejidad,
		models.Concertacion_Tema.conc_actores_externos,
		#Datos de Estudiante
		models.Estudiante.est_genero,  
		models.Estudiante.est_estado_civil,
		models.Estudiante.est_trabajo,
		models.Estudiante.est_becado,  
		models.Estudiante.est_hijos, 
		models.Estudiante.est_posibilidad_economica,
		models.Estudiante.est_trab_remoto,
	).select_from(models.Actividades_Tarea		
	).join(models.Asignacion_Tarea, models.Asignacion_Tarea.id_asignacion == models.Actividades_Tarea.id_asg_act
	).join(models.Tipo_Tarea, models.Tipo_Tarea.id_tipo_tarea == models.Asignacion_Tarea.asg_tipo_tarea_id
	).join(models.Concertacion_Tema, models.Concertacion_Tema.id_conc_tema == models.Asignacion_Tarea.asg_conc_id
	).join(models.Estudiante, models.Estudiante.id_estudiante == models.Asignacion_Tarea.asg_estudiante_id
	).join(est_query, est_query.c.est_user_id == models.Estudiante.user_estudiante_id		
	).statement
					   
	datos = pd.read_sql(db_actividades_asig, con=engine)	
	#Preparando datos
	print(datos.describe())
	
						
	return {"Return":"Res"}
	