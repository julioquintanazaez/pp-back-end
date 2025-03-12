from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Cliente
from schemas.cliente import Cliente_Record, ClienteAdd, Cliente_InDB
from schemas.user import User_InDB
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

router = APIRouter()

@router.post("/crear_cliente/", status_code=status.HTTP_201_CREATED)
async def crear_cliente(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					cliente: ClienteAdd, db: Session = Depends(get_db)):
	try:
		db_cliente = Cliente(
			cli_numero_empleos = cliente.cli_numero_empleos,
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
		return db_cliente 
	except IntegrityError as e:
		raise HTTPException(status_code=500, detail="Error de integridad creando objeto Cliente")
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Error inesperado creando el objeto Cliente")		


@router.get("/leer_cliente/", status_code=status.HTTP_201_CREATED)  
async def leer_cliente(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

		return db.query(Cliente).offset(skip).limit(limit).all() 


@router.delete("/eliminar_cliente/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_cliente(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_cliente = db.query(Cliente).filter(Cliente.id_cliente == id).first()
	if db_cliente is None:
		raise HTTPException(status_code=404, detail="El cliente no existe en la base de datos")	
	db.delete(db_cliente)	
	db.commit()
	db.refresh(db_cliente)	
	return {"Result": "Cliente eliminado satisfactoriamente"}
	

@router.put("/actualizar_cliente/{id}", status_code=status.HTTP_201_CREATED) 
async def actualizar_cliente(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["cliente"])], 
				id: str, cliente: Cliente_Record, db: Session = Depends(get_db)):
	
	db_cliente = db.query(Cliente).filter(Cliente.id_cliente == id).first()
	if db_cliente is None:
		raise HTTPException(status_code=404, detail="El cliente seleccionado no existen en la base de datos")
	db_cliente.cli_numero_empleos = cliente.cli_numero_empleos
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
	
