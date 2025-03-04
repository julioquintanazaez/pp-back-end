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

from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError
from typing_extensions import Annotated
from security.auth import create_access_token, authenticate_user, get_current_active_user, get_current_user
from db.database import SessionLocal, engine 
import core.config as config
import asyncio
import concurrent.futures
import csv
from io import BytesIO, StringIO
from fastapi.responses import StreamingResponse

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

from routers.user import users
from routers.security import auth

#Create our main app
app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)

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

ALGORITHM = config.ALGORITHM	
SECRET_KEY = config.SECRET_KEY
APP_NAME = config.APP_NAME
ADMIN_USER = config.ADMIN_USER
ADMIN_NOMBRE = config.ADMIN_NOMBRE
ADMIN_PAPELLIDO = config.ADMIN_PAPELLIDO
ADMIN_SAPELLIDO = config.ADMIN_SAPELLIDO
ADMIN_CI = config.ADMIN_CI
ADMIN_CORREO = config.ADMIN_CORREO
ADMIN_PASS = config.ADMIN_PASS


@app.get("/")
def index():
	return {"Application": "Hello from developers"}
	
