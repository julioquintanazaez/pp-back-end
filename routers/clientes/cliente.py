from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, get_db
from models.data import Cliente, User
from schemas.cliente import Cliente_Record, ClienteAdd, Cliente_InDB, ClienteSchema
from schemas.user import User_InDB
from security.auth import get_current_active_user, get_current_user
from typing_extensions import Annotated
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List

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
			cli_centro_id = cliente.cli_centro_id,
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


@router.delete("/eliminar_cliente/{id}", status_code=status.HTTP_201_CREATED) 
async def eliminar_cliente(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					id: str, db: Session = Depends(get_db)):
	db_cliente = db.query(Cliente).filter(Cliente.id_cliente == id).first()
	if db_cliente is None:
		raise HTTPException(status_code=404, detail="El cliente no existe en la base de datos")	
	db.delete(db_cliente)	
	db.commit()
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
	

@router.get("/leer_clientes/", response_model=List[ClienteSchema], status_code=status.HTTP_201_CREATED)  
async def leer_clientes(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["admin"])],
					skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    

	db_clientes = db.query(
			#Datos cliente
			Cliente.id_cliente,
			Cliente.cli_numero_empleos,
			Cliente.cli_pos_tecnica_trabajo,
			Cliente.cli_pos_tecnica_hogar, 
			Cliente.cli_cargo,
			Cliente.cli_trab_remoto, 
			Cliente.cli_categoria_docente,
			Cliente.cli_categoria_cientifica,
			Cliente.cli_experiencia_practicas, 
			Cliente.cli_numero_est_atendidos,
			#Datos del usuario
			User.id,
			User.ci,
			User.nombre,
			User.primer_appellido,
			User.segundo_appellido,
			User.email,							
			).select_from(Cliente
			).join(User, User.id == Cliente.user_cliente_id	
			).all()	
	# Serializar los datos
	result = [
        {
            "id_cliente": cliente[0],
            "cli_numero_empleos": cliente[1],
			"cli_pos_tecnica_trabajo": cliente[2],
			"cli_pos_tecnica_hogar": cliente[3], 
			"cli_cargo": cliente[4],
			"cli_trab_remoto": cliente[5], 
			"cli_categoria_docente": cliente[6],
			"cli_categoria_cientifica" : cliente[7],
			"cli_experiencia_practicas": cliente[8], 
			"cli_numero_est_atendidos": cliente[9],
            "usuario_id": cliente[10],
            "ci": cliente[11],
            "nombre": cliente[12],
            "primer_appellido": cliente[13],
            "segundo_appellido": cliente[14],
            "email": cliente[15],
        }
        for cliente in db_clientes
    ]
    
	return result

