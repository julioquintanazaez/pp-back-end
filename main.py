from fastapi import FastAPI
from functools import lru_cache
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4

import core.config as config
from routers.user import users
from routers.security import auth
from routers.universidades import universidad
from routers.centro import centropracticas
from routers.profesores import profesor
from routers.clientes import cliente
from routers.estudiantes import estudiante
from routers.tareas import tarea
from routers.concertaciones import concertacion

#Create our main app "https://pp-back-end.onrender.com"
app = FastAPI()

app.include_router(auth.router)  #, prefix="/auth", tags=["auth"]
app.include_router(users.router, prefix="/usuario", tags=["usuario"])
app.include_router(universidad.router, prefix="/universidad", tags=["universidad"])
app.include_router(centropracticas.router, prefix="/centro", tags=["centro"])
app.include_router(profesor.router, prefix="/profesor", tags=["profesor"])
app.include_router(estudiante.router, prefix="/estudiante", tags=["estudiante"])
app.include_router(cliente.router, prefix="/cliente", tags=["cliente"])
app.include_router(tarea.router, prefix="/tarea", tags=["tarea"])
app.include_router(concertacion.router, prefix="/concertacion", tags=["concertacion"])


# Allow these methods to be used
methods = ["GET", "POST", "PUT", "DELETE"]

# Only these headers are allowed
headers = ["Content-Type", "Authorization"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=config.CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=methods,
	allow_headers=headers,
	expose_headers=["*"]
)

@app.get("/")
def index():
	return {"Aplicación": "Prácticas profesionales"}
	
