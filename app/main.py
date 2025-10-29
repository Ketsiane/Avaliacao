from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import produtos
from app.database import create_db_and_tables # Importa a função de criação de tabelas

# 1. NOVO PADRÃO: Define o ciclo de vida da aplicação (startup e shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de STARTUP (Executada antes de o servidor aceitar requisições)
    print("Iniciando Microsserviço: Criando tabelas no banco de dados...")
    create_db_and_tables()
    yield
    # Lógica de SHUTDOWN (Executada quando o servidor está desligando)
    print("Microsserviço desligado.")
    # Você adicionaria a lógica de fechamento de conexões se necessário aqui.


# 2. INSTÂNCIA: Passa a função lifespan para o FastAPI
app = FastAPI(
    title="API de Produtos - FastAPI + Render", 
    lifespan=lifespan # Usa o novo padrão
)

# 3. ROTAS: Inclui o router de produtos
app.include_router(produtos.router)

@app.get("/")
def home():
    return {"message": "API de Produtos - FastAPI + PostgreSQL no Render"}