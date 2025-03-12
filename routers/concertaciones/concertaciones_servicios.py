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


@router.post("/mostrar_concertacion/", status_code=status.HTTP_201_CREATED)
async def mostrar_concertacion(current_user: Annotated[User_InDB, Security(get_current_user, scopes=["profesor", "cliente"])],
					concertacion: ConcertacionAdd, db: Session = Depends(get_db)):
	
    return ""