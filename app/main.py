from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import fila as fila_router # Importa o novo router de fila
from app.database import create_db_and_tables # Reutiliza a função de criação de DB

# 1. Define o ciclo de vida da aplicação (executa antes de iniciar o servidor)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de STARTUP: Cria as tabelas
    print("Iniciando API Fila: Criando tabelas no banco de dados...")
    create_db_and_tables()
    yield
    # Lógica de SHUTDOWN (opcional)
    print("API Fila desligada.")

app = FastAPI(
    title="API Fila de Atendimento - Totem", 
    lifespan=lifespan 
)

# Inclui o router de fila
app.include_router(fila_router.router) 

@app.get("/")
def home():
    return {"message": "API Fila de Atendimento - OK"}