import os
import hashlib
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
import streamlit as st

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_admin = Column(Boolean, default=False)

class Recoleccion(Base):
    __tablename__ = 'recolecciones'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    fecha = Column(String)  
    ubicacion = Column(String)
    operador = Column(String)
    notas = Column(String)
    tipos = Column(String)
    cantidades = Column(String)
    impacto_total = Column(Float)
    fauna_afectada = Column(Float)

class Wte(Base):
    __tablename__ = 'wte'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    fecha = Column(String)
    e_mj = Column(Float)
    e_kwh = Column(Float)
    masa_kg = Column(Float)

# --- INICIALIZACIÓN ---
def get_engine():
    # Si hay secretos configurados en Streamlit Cloud para Supabase (u otro Postgres), se usará.
    # Si no, hará fallback a un archivo SQLite local automáticamente.
    try:
        db_url = st.secrets["DB_URL"]
    except Exception:
        db_url = "sqlite:///iiae_local.db"
    
    # En Supabase/Postgres desde SQLAlchemy a veces requiere 'postgresql://' envés de 'postgres://'
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(db_url, connect_args={'check_same_thread': False} if 'sqlite' in db_url else {})
    Base.metadata.create_all(engine)
    return engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

# --- AUTENTICACIÓN ---
def hash_password(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return (salt + key).hex()

def verify_password(stored_password, provided_password: str) -> bool:
    # Convertimos de vuelta de hexadecimal a bytes (y soportamos bytes por compatibilidad)
    stored_bytes = bytes.fromhex(stored_password) if isinstance(stored_password, str) else stored_password
    salt = stored_bytes[:32]
    key = stored_bytes[32:]
    new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return key == new_key

def authenticate_user(username, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(user.password_hash, password):
            return user
        return None
    finally:
        db.close()

def register_user(username, password, is_admin=False):
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            return False, "El nombre de usuario ya existe."
        hashed_pw = hash_password(password)
        new_user = User(username=username, password_hash=hashed_pw, is_admin=is_admin)
        db.add(new_user)
        db.commit()
        return True, "Registro exitoso."
    finally:
        db.close()

# --- OPERACIONES DE DATOS ---

def load_historial(user_id=None, is_admin=False) -> pd.DataFrame:
    db = SessionLocal()
    try:
        query = db.query(Recoleccion)
        if not is_admin and user_id is not None:
            query = query.filter(Recoleccion.user_id == user_id)
        
        data = query.all()
        columns = ["Fecha", "Ubicación", "Operador", "Notas", "Tipos", "Cantidades (kg)", "Impacto total", "Fauna afectada"]
        if not data:
            return pd.DataFrame(columns=columns)
            
        rows = [[d.fecha, d.ubicacion, d.operador, d.notas, d.tipos, d.cantidades, d.impacto_total, d.fauna_afectada] for d in data]
        df = pd.DataFrame(rows, columns=columns)
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce')
        return df
    finally:
        db.close()

def save_historial(user_id: int, fecha: str, tipos: list, cantidades: list, total: float, fauna: float,
                   ubicacion: str = "", operador: str = "", notas: str = "") -> None:
    db = SessionLocal()
    try:
        rec = Recoleccion(
            user_id=user_id,
            fecha=fecha,
            ubicacion=ubicacion,
            operador=operador,
            notas=notas,
            tipos=", ".join(tipos),
            cantidades=", ".join(map(str, cantidades)),
            impacto_total=float(total),
            fauna_afectada=float(fauna)
        )
        db.add(rec)
        db.commit()
    finally:
        db.close()

def load_wte_historial(user_id=None, is_admin=False) -> pd.DataFrame:
    db = SessionLocal()
    try:
        query = db.query(Wte)
        if not is_admin and user_id is not None:
            query = query.filter(Wte.user_id == user_id)
        
        data = query.all()
        cols = ["Fecha", "E_MJ", "E_kWh", "Masa_kg"]
        if not data:
            return pd.DataFrame(columns=cols)
            
        rows = [[d.fecha, d.e_mj, d.e_kwh, d.masa_kg] for d in data]
        return pd.DataFrame(rows, columns=cols)
    finally:
        db.close()

def save_wte_historial(user_id: int, fecha: str, e_mj: float, e_kwh: float, masa_kg: float) -> None:
    db = SessionLocal()
    try:
        wte_rec = Wte(
            user_id=user_id,
            fecha=fecha,
            e_mj=float(e_mj),
            e_kwh=float(e_kwh),
            masa_kg=float(masa_kg)
        )
        db.add(wte_rec)
        db.commit()
    finally:
        db.close()

def clear_historial(user_id: int, is_admin: bool = False):
    db = SessionLocal()
    try:
        if is_admin:
            db.query(Recoleccion).delete()
            db.query(Wte).delete()
        else:
            db.query(Recoleccion).filter(Recoleccion.user_id == user_id).delete()
            db.query(Wte).filter(Wte.user_id == user_id).delete()
        db.commit()
    finally:
        db.close()

def delete_user(user_id: int):
    db = SessionLocal()
    try:
        db.query(Recoleccion).filter(Recoleccion.user_id == user_id).delete()
        db.query(Wte).filter(Wte.user_id == user_id).delete()
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()

def change_password(user_id: int, old_password: str, new_password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user and verify_password(user.password_hash, old_password):
            user.password_hash = hash_password(new_password)
            db.commit()
            return True, "Contraseña actualizada."
        return False, "La contraseña actual es incorrecta."
    finally:
        db.close()
