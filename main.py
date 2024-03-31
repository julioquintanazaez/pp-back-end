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
from fpdf import FPDF
from fpdf_table import PDFTable, Align, add_image_local
import asyncio
import concurrent.futures
import csv
from io import BytesIO, StringIO
from fastapi.responses import StreamingResponse

models.Base.metadata.create_all(bind=engine)

#Create resources for JWT flow
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
	tokenUrl="token",
	scopes={"admin": "Add, edit and delete information.", "manager": "Create and read information.", "user": "Read information."}
)
#----------------------
#Create our main app
app = FastAPI()

#----SETUP MIDDLEWARES--------------------

# Allow these origins to access the API
origins = [	
	"http://my-app-4bad.onrender.com",
	"https://my-app-4bad.onrender.com",		
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
ADMIN_NAME = config.ADMIN_NAME
ADMIN_EMAIL = config.ADMIN_EMAIL
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
	print(user.role)
	access_token = create_access_token(
		data={"sub": user.username, "scopes": user.role},   #form_data.scopes
		expires_delta=access_token_expires
	)
	return {"detail": "Ok", "access_token": access_token, "token_type": "Bearer"}
	
@app.get("/")
def index():
	return {"Application": "Hello from developers"}
	
@app.get("/get_restricted_user")
async def get_restricted_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)]):
    return current_user
	
@app.get("/get_authenticated_admin_resources", response_model=schemas.User)
async def get_authenticated_admin_resources(current_user: Annotated[schemas.User, Security(get_current_active_user, scopes=["manager"])]):
    return current_user
	
@app.get("/get_authenticated_edition_resources", response_model=schemas.User)
async def get_authenticated_edition_resources(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])]):
    return current_user
	
@app.get("/get_user_status", response_model=schemas.User)
async def get_user_status(current_user: Annotated[schemas.User, Depends(get_current_user)]):
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
		full_name=config.ADMIN_NAME,
		email=config.ADMIN_EMAIL,
		role=["admin","manager","user"],
		disable=False,
		hashed_password=pwd_context.hash(config.ADMIN_PASS)		
	)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)	
	return {f"User:": "Succesfully created"}
	
@app.post("/create_user/", status_code=status.HTTP_201_CREATED)  
async def create_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				user: schemas.UserInDB, db: Session = Depends(get_db)): 
	if db.query(models.User).filter(models.User.username == user.username).first() :
		raise HTTPException( 
			status_code=400,
			detail="The user with this email already exists in the system",
		)	
	db_user = models.User(
		username=user.username, 
		full_name=user.full_name,
		email=user.email,
		role=user.role,
		disable=False,
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
	db_user.username=new_user.username
	db_user.full_name=new_user.full_name
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
async def reset_password(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
				username: str, password: schemas.UserPassword, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="User not found")	
	db_user.hashed_password=pwd_context.hash(password.hashed_password)
	db.commit()
	db.refresh(db_user)	
	return {"Result": "Password Updated Successfuly"}
	
@app.put("/reset_password_by_user/{username}", status_code=status.HTTP_201_CREATED) 
async def reset_password_by_user(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
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
async def crear_entidad_origen(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
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

@app.get("/leer_entidades_origen/")  
async def leer_entidades_origen(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_entidades = db.query(models.Entidad_Origen).all()	
	
	return db_entidades
	
@app.delete("/eliminar_entidad_origen/{id}") 
async def eliminar_entidad_origen(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_entidad = db.query(models.Entidad_Origen
						).filter(models.Entidad_Origen.id_entidad_origen == id
						).first()
	if db_entidad is None:
		raise HTTPException(status_code=404, detail="La Entidad Origen no existe en la base de datos")	
	db.delete(db_entidad)	
	db.commit()
	return {"Result": "Entidad origen eliminada satisfactoriamente"}
	
#############################
####  ENTIDAD DESTINO #######
#############################
@app.post("/crear_entidad_destino/", status_code=status.HTTP_201_CREATED)
async def crear_entidad_destino(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
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

@app.get("/leer_entidades_destino/")  
async def leer_entidades_destino(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_entidades = db.query(models.Entidad_Destino).all()	
	
	return db_entidades
	
@app.delete("/eliminar_entidad_destino/{id}") 
async def eliminar_entidad_destino(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_entidad = db.query(models.Entidad_Destino
						).filter(models.Entidad_Destino.id_entidad_destino == id
						).first()
	if db_entidad is None:
		raise HTTPException(status_code=404, detail="La Entidad Destino no existe en la base de datos")	
	db.delete(db_entidad)	
	db.commit()
	return {"Result": "Entidad destino eliminada satisfactoriamente"}
	
#############################
#######  PROFESOR  ##########
#############################
@app.post("/crear_profesor/", status_code=status.HTTP_201_CREATED)
async def crear_profesor(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					profesor: schemas.Profesor, db: Session = Depends(get_db)):
	try:
		db_profesor = models.Profesor(
			prf_ci = profesor.prf_ci,
			prf_nombre = profesor.prf_nombre,
			prf_primer_appellido = profesor.prf_primer_appellido,
			prf_segundo_appellido = profesor.prf_segundo_appellido,
			prf_correo = profesor.prf_correo,
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
			prf_entidad_id = profesor.prf_entidad_id		
		)			
		db.add(db_profesor)   	
		db.commit()
		db.refresh(db_profesor)			
		return db_profesor
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Profesor")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Profesor")		

@app.get("/leer_profesores/")  
async def leer_profesores(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_profesores = db.query(models.Profesor).all()	
	
	return db_profesores
	
@app.delete("/eliminar_profesor/{id}") 
async def eliminar_profesor(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_profesor = db.query(models.Profesor
						).filter(models.Profesor.id_profesor == id
						).first()
	if db_profesor is None:
		raise HTTPException(status_code=404, detail="El profesor no existe en la base de datos")	
	db.delete(db_profesor)	
	db.commit()
	return {"Result": "Profesor eliminado satisfactoriamente"}

#############################
#######  ESTUDIANTE  ########
#############################
@app.post("/crear_estudiante/", status_code=status.HTTP_201_CREATED)
async def crear_estudiante(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					estudiante: schemas.Estudiante, db: Session = Depends(get_db)):
	try:
		db_estudiante = models.Estudiante(
			est_ci = estudiante.est_ci,
			est_nombre = estudiante.est_nombre,
			est_primer_appellido = estudiante.est_primer_appellido,
			est_segundo_appellido = estudiante.est_segundo_appellido,  
			est_correo = estudiante.est_correo, 
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
		)			
		db.add(db_estudiante)   	
		db.commit()
		db.refresh(db_estudiante)			
		return db_estudiante
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Estudiante")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Estudiante")		

@app.get("/leer_estudiante/")  
async def leer_estudiante(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_estudiantes = db.query(models.Estudiante).all()	
	
	return db_estudiantes
	
@app.delete("/eliminar_estudiante/{id}") 
async def eliminar_estudiante(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_estudiante = db.query(models.Estudiante
						).filter(models.Estudiante.id_estudiante == id
						).first()
	if db_estudiante is None:
		raise HTTPException(status_code=404, detail="El estudiante no existe en la base de datos")	
	db.delete(db_estudiante)	
	db.commit()
	return {"Result": "Estudiante eliminado satisfactoriamente"}

#############################
#######   CLIENTE  ##########
#############################
@app.post("/crear_cliente/", status_code=status.HTTP_201_CREATED)
async def crear_cliente(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					cliente: schemas.Cliente, db: Session = Depends(get_db)):
	try:
		db_cliente = models.Cliente(
			cli_ci = cliente.cli_ci,
			cli_nombre = cliente.cli_nombre,
			cli_primer_appellido = cliente.cli_primer_appellido,			
			cli_segundo_appellido = cliente.cli_segundo_appellido, 
			cli_correo = cliente.cli_correo,
			cli_genero = cliente.cli_genero,
			cli_estado_civil = cliente.cli_estado_civil,  #Soltero, Casado, Divorciado, Viudo
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
			cli_entidad_id = cliente.cli_entidad_id 		
		)			
		db.add(db_cliente)   	
		db.commit()
		db.refresh(db_cliente)			
		return db_cliente
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Cliente")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Cliente")		

@app.get("/leer_cliente/")  
async def leer_cliente(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_cliente = db.query(models.Cliente).all()	
	
	return db_cliente
	
@app.delete("/eliminar_cliente/{id}") 
async def eliminar_cliente(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_cliente = db.query(models.Cliente
						).filter(models.Cliente.id_cliente == id
						).first()
	if db_cliente is None:
		raise HTTPException(status_code=404, detail="El cliente no existe en la base de datos")	
	db.delete(db_cliente)	
	db.commit()
	return {"Result": "Cliente eliminado satisfactoriamente"}
	
#############################
###  CONCERTACION TEMA ######
#############################
@app.post("/crear_concertacion_tema/", status_code=status.HTTP_201_CREATED)
async def crear_concertacion_tema(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
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
		)			
		db.add(db_concertacion)   	
		db.commit()
		db.refresh(db_concertacion)			
		return db_concertacion
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Cliente")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Cliente")		

@app.get("/leer_concertaciones/")  
async def leer_concertaciones(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_concertacion = db.query(models.Concertacion_Tema).all()	
	
	return db_concertacion
	
@app.delete("/eliminar_concertacion/{id}") 
async def eliminar_concertacion(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_concertacion = db.query(models.Concertacion_Tema
						).filter(models.Concertacion_Tema.id_conc_tema == id
						).first()
	if db_concertacion is None:
		raise HTTPException(status_code=404, detail="La concertacion no existe en la base de datos")	
	db.delete(db_concertacion)	
	db.commit()
	return {"Result": "Concertacion eliminada satisfactoriamente"}
	
@app.put("/evaluar_concertacion/{id}") 
async def evaluar_concertacion(current_user: Annotated[schemas.User, Depends(get_current_active_user)], 
				id: str, conc_eva: schemas.Concertacion_Tema_Eval, db: Session = Depends(get_db)):
	db_concertacion = db.query(models.Concertacion_Tema).filter(models.Concertacion_Tema.id_conc_tema == id).first()
	if db_concertacion is None:
		raise HTTPException(status_code=404, detail="Concertacion no existe ne base de datos")
	db_concertacion.conc_evaluacion = conc_eva.conc_evaluacion 	
	db.commit()
	db.refresh(db_concertacion)	
	return db_concertacion
	
#############################
####### TIPO TAREA  #########
#############################
@app.post("/crear_tipo_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_tipo_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
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

@app.get("/leer_tipos_tareas/")  
async def leer_tipos_tareas(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_tipos_tareas = db.query(models.Tipo_Tarea).all()	
	
	return db_tipos_tareas
	
@app.delete("/eliminar_tipo_tarea/{id}") 
async def eliminar_tipo_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_tipo_tarea = db.query(models.Tipo_Tarea
						).filter(models.Tipo_Tarea.id_tipo_tarea == id
						).first()
	if db_tipo_tarea is None:
		raise HTTPException(status_code=404, detail="El tipo de tarea no existe en la base de datos")	
	db.delete(db_tipo_tarea)	
	db.commit()
	return {"Result": "Tarea eliminada satisfactoriamente"}
	
#############################
###  ASIGNACION TAREA  ######
#############################
@app.post("/crear_asignacion_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_asignacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					asg_tarea: schemas.Asignacion_Tarea, db: Session = Depends(get_db)):
	try:
		db_asg_tarea = models.Asignacion_Tarea(
			asg_descripcion = asg_tarea.asg_descripcion,
			asg_fecha_inicio = asg_tarea.asg_fecha_inicio, 
			asg_fecha_fin = asg_tarea.asg_fecha_fin, 
			asg_complejidad_estimada = asg_tarea.asg_complejidad_estimada, 
			asg_participantes = asg_tarea.asg_participantes,  #Numero de miembros en el equipo
			#asg_evaluacion = asg_tarea.asg_evaluacion,  # con average de actividades
			#asg_asignada = asg_tarea.asg_asignada, 
			asg_tipo_tarea_id = asg_tarea.asg_tipo_tarea_id,
			asg_estudiante_id = asg_tarea.asg_estudiante_id,    
			asg_conc_id = asg_tarea.asg_conc_id
		)			
		db.add(db_asg_tarea)   	
		db.commit()
		db.refresh(db_asg_tarea)			
		return db_asg_tarea
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Asignacion_Tareas")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Asignacion_Tareas")		

@app.get("/leer_asgignaciones_tareas/")  
async def leer_asgignaciones_tareas(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_asgnaciones_tareas = db.query(models.Asignacion_Tarea).all()	
	
	return db_asgnaciones_tareas
	
@app.delete("/eliminar_asgignacion_tarea/{id}") 
async def eliminar_asgignacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_asg_tarea = db.query(models.Asignacion_Tarea
						).filter(models.Asignacion_Tarea.id_asignacion == id
						).first()
	if db_asg_tarea is None:
		raise HTTPException(status_code=404, detail="La asignacion no existe en la base de datos")	
	db.delete(db_asg_tarea)	
	db.commit()
	return {"Result": "Asignacion de Tarea eliminada satisfactoriamente"}

@app.put("/evaluar_asignacion_tarea/{id}") 
async def evaluar_asignacion_tarea(current_user: Annotated[schemas.User, Depends(get_current_active_user)], 
				id: str, asg_tarea_eva: schemas.Asignacion_Tarea_Eval, db: Session = Depends(get_db)):
	db_asg_tarea = db.query(models.Asignacion_Tarea).filter(models.Asignacion_Tarea.id_asignacion == id).first()
	if db_asg_tarea is None:
		raise HTTPException(status_code=404, detail="Tarea no existe ne la base de datos")
	db_asg_tarea.asg_evaluacion = asg_tarea_eva.asg_evaluacion 	
	db.commit()
	db.refresh(db_asg_tarea)	
	return db_asg_tarea
	
#############################
###  ACTIVIDADES TAREA  #####
#############################
@app.post("/crear_actividad_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_actividad_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					act_tarea: schemas.Actividades_Tarea, db: Session = Depends(get_db)):
	try:
		db_act_tarea = models.Actividades_Tarea(
			act_nombre = act_tarea.act_nombre,
			#act_resultado = act_tarea.act_resultado, 
			act_est_memo = act_tarea.act_est_memo,
			act_prof_memo = act_tarea.act_prof_memo,
			act_cli_memo = act_tarea.act_cli_memo,
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

@app.get("/leer_actividades_tareas/")  
async def leer_actividades_tareas(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_actividades_tareas = db.query(models.Actividades_Tarea).all()	
	
	return db_actividades_tareas
	
@app.delete("/eliminar_actividad_tarea/{id}") 
async def eliminar_actividad_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_act_tarea = db.query(models.Actividades_Tarea
						).filter(models.Actividades_Tarea.id_actividad_tarea == id
						).first()
	if db_act_tarea is None:
		raise HTTPException(status_code=404, detail="La actividad no existe en la base de datos")	
	db.delete(db_act_tarea)	
	db.commit()
	return {"Result": "Actividad de Tarea eliminada satisfactoriamente"}
	
@app.put("/evaluar_actividad_tarea/{id}") 
async def evaluar_actividad_tarea(current_user: Annotated[schemas.User, Depends(get_current_active_user)], 
				id: str, act_tarea_eva: schemas.Actividades_Tarea_Eval, db: Session = Depends(get_db)):
	db_act_tarea = db.query(models.Actividades_Tarea).filter(models.Actividades_Tarea.id_actividad_tarea == id).first()
	if db_act_tarea is None:
		raise HTTPException(status_code=404, detail="Actividad Tarea no existe ne la base de datos")
	db_act_tarea.act_resultado = act_tarea_eva.act_resultado 	
	db.commit()
	db.refresh(db_act_tarea)	
	return db_act_tarea
	
#############################
###  ACTUALIZACION TAREA  ###
#############################
@app.post("/crear_actualizacion_tarea/", status_code=status.HTTP_201_CREATED)
async def crear_actualizacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					act_tarea: schemas.Tareas_Actualizacion, db: Session = Depends(get_db)):
	try:
		db_act_tarea = models.Tareas_Actualizacion(
			fecha_actualizacion = act_tarea.fecha_actualizacion,
			memo_actualizacion = act_tarea.memo_actualizacion, 
			id_asg_upd = act_tarea.id_asg_upd,
		)			
		db.add(db_act_tarea)   	
		db.commit()
		db.refresh(db_act_tarea)			
		return db_act_tarea
		
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Tareas_Actualizacion")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Tareas_Actualizacion")	

@app.get("/leer_actualizaciones_tareas/")  
async def leer_actualizaciones_tareas(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	db_actualizaciones_tareas = db.query(models.Tareas_Actualizacion).all()	
	
	return db_actualizaciones_tareas
	
@app.delete("/eliminar_actualizacion_tarea/{id}") 
async def eliminar_actualizacion_tarea(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					id: str, db: Session = Depends(get_db)):
	db_act_tarea = db.query(models.Tareas_Actualizacion
						).filter(models.Tareas_Actualizacion.id_tareas_act == id
						).first()
	if db_act_tarea is None:
		raise HTTPException(status_code=404, detail="La actividad no existe en la base de datos")	
	db.delete(db_act_tarea)	
	db.commit()
	return {"Result": "Actividad de Tarea eliminada satisfactoriamente"}

#############################
###  CONSULTAS A LA BD    ###
#############################
@app.get("/obtener_registros_concertaciones/")  
async def obtener_registros_concertaciones(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):  
	
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
							models.Profesor.prf_nombre,
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
							models.Cliente.cli_nombre,
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
							).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id
							).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
							).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id							
							).all()	
	
	return db_concertaciones 
	
@app.get("/obtener_registros_asignaciones/")  
async def obtener_registros_asignaciones(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):  
	
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
							models.Estudiante.est_nombre, 
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
							).all()	
	
	return db_asignaciones 

@app.get("/obtener_registros_actividades/")  
async def obtener_registros_actividades(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
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
async def obtener_registros_actividades_asignacion(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):  
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
							models.Estudiante.est_nombre, 
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
							).all()	
	
	return db_actividades_asig 
	
#############################
#######    ACER PDF    ######
#############################
def create_csv(query, columns_names):
	csvtemp = ""		
	header = [i for i in columns_names]
	csvtemp = ",".join(header) + "\n"
	
	for row in query:		
		csvtemp += (str(row)).replace("(", "").replace(")", "").replace("'", "") + "\n"		
		
	return StringIO(csvtemp)
	
@app.get("/pdf_registros_concertaciones/")  
async def pdf_registros_concertaciones(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					db: Session = Depends(get_db)):  	
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
							models.Profesor.prf_nombre,
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
							models.Cliente.cli_nombre,
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
							models.Entidad_Origen.id_entidad_origen,
							models.Entidad_Origen.org_siglas,
							models.Entidad_Origen.org_transporte,
							models.Entidad_Origen.org_trab_remoto,
							#Datos Entidad Destino							
							models.Entidad_Destino.id_entidad_destino,
							models.Entidad_Destino.dest_siglas,
							models.Entidad_Destino.dest_transporte,
							models.Entidad_Destino.dest_experiencia,
							models.Entidad_Destino.dest_trab_remoto,
							).select_from(models.Concertacion_Tema
							).join(models.Profesor, models.Profesor.id_profesor == models.Concertacion_Tema.conc_profesor_id
							).join(models.Cliente, models.Cliente.id_cliente == models.Concertacion_Tema.conc_cliente_id
							).join(models.Entidad_Origen, models.Entidad_Origen.id_entidad_origen == models.Profesor.prf_entidad_id
							).join(models.Entidad_Destino, models.Entidad_Destino.id_entidad_destino == models.Cliente.cli_entidad_id							
							).all()	
					
	columns_conc = ["id_conc_tema","conc_tema","conc_descripcion","conc_complejidad","conc_valoracion_prof","conc_profesor_id","conc_actores_externos","conc_evaluacion","conc_valoracion_cliente","conc_cliente_id"]
	columns_prf = ["id_profesor","prf_nombre","prf_genero","prf_estado_civil","prf_numero_empleos","prf_hijos","prf_cargo","prf_categoria_docente","prf_categoria_cientifica","prf_experiencia_practicas","prf_numero_est_atendidos","prf_trab_remoto"]
	columns_cli = ["id_cliente","cli_nombre","cli_genero","cli_estado_civil","cli_numero_empleos","cli_hijos","cli_cargo","cli_categoria_docente","cli_categoria_cientifica","cli_experiencia_practicas","cli_numero_est_atendidos","cli_trab_remoto"]
	columns_org = ["id_entidad_origen","org_siglas","org_transporte","org_trab_remoto"]
	columns_des = ["id_entidad_destino","dest_siglas","dest_transporte","dest_experiencia","dest_trab_remoto"]
	columns = columns_conc + columns_prf + columns_cli + columns_org + columns_des
	
	myfile = create_csv(db_concertaciones, columns)	
	headers = {'Content-Disposition': 'attachment; filename="concertaciones.csv"'} 
	return StreamingResponse(iter([myfile.getvalue()]), media_type="application/csv", headers=headers)		  
	
@app.get("/pdf_registros_asignaciones/")  
async def pdf_registros_asignaciones(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					db: Session = Depends(get_db)):  	
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
							models.Estudiante.est_nombre, 
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
							).all()	
	
	columns_asg=["id_asignacion","asg_descripcion","asg_fecha_inicio","asg_complejidad_estimada","asg_participantes","asg_evaluacion","asg_tipo_tarea_id","asg_estudiante_id","asg_conc_id","asg_evaluacion"]
	columns_tipo=["id_tipo_tarea","tarea_tipo_nombre"]
	columns_conc=["id_conc_tema","conc_tema","conc_descripcion","conc_complejidad","conc_valoracion_prof","conc_profesor_id","conc_valoracion_cliente","conc_cliente_id","conc_actores_externos","conc_evaluacion"]
	columns_est=["id_estudiante","est_nombre","est_genero","est_estado_civil","est_trabajo","est_becado","  est_hijos"," est_posibilidad_economica","est_entidad_id","est_trab_remoto"]
	columns = columns_asg + columns_tipo + columns_conc + columns_est
	
	myfile = create_csv(db_asignaciones, columns)	
	headers = {'Content-Disposition': 'attachment; filename="asignaciones.csv"'} 
	return StreamingResponse(iter([myfile.getvalue()]), media_type="application/csv", headers=headers)	

@app.get("/pdf_registros_actividades/")  
async def pdf_registros_actividades(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					db: Session = Depends(get_db)):  
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
	
	myfile = create_csv(db_actividades, models.Actividades_Tarea.__table__.columns.keys())	
	headers = {'Content-Disposition': 'attachment; filename="actividades.csv"'} 
	return StreamingResponse(iter([myfile.getvalue()]), media_type="application/csv", headers=headers)	
		
@app.get("/pdf_registros_actividades_asignacion/")  
async def pdf_registros_actividades_asignacion(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["manager"])],
					db: Session = Depends(get_db)):  
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
							models.Estudiante.est_nombre, 
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
							).all()	
	columns_act = ["id_actividad_tarea","act_nombre","act_resultado","act_est_memo","act_prof_memo","act_cli_memo","id_asg_act","act_resultado"]
	columns_asg = ["id_asignacion","asg_descripcion","asg_fecha_inicio","asg_complejidad_estimada","asg_participantes","asg_evaluacion","asg_tipo_tarea_id","asg_estudiante_id","asg_conc_id"]
	columns_tipo = ["id_tipo_tarea","tarea_tipo_nombre"]
	columns_conc = ["id_conc_tema","conc_tema","conc_descripcion","conc_complejidad","conc_valoracion_prof","conc_profesor_id","conc_valoracion_cliente","conc_cliente_id","conc_actores_externos","conc_evaluacion"]
	columns_est = ["id_estudiante","est_nombre","est_genero","est_estado_civil","est_trabajo","est_becado","est_hijos","est_posibilidad_economica","est_entidad_id","est_trab_remoto"]
	columns = columns_act + columns_asg + columns_tipo + columns_conc + columns_est
	
	myfile = create_csv(db_actividades_asig, columns)	
	headers = {'Content-Disposition': 'attachment; filename="actividades_asignacion.csv"'} 
	return StreamingResponse(iter([myfile.getvalue()]), media_type="application/csv", headers=headers)	