# back-end/db/create_db.py
from sqlmodel import SQLModel
from db.db import engine
import db.models  # importa i modelli

print("🔧 Creazione tabelle nel database...")
SQLModel.metadata.create_all(engine)
print("✅ Tabelle create correttamente!")
