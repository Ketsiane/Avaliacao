from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime, timezone # Importar timezone para UTC

class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(max_length=20, index=True)
    
    # Ajuste para usar UTC (padrão robusto para DB)
    data_chegada: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Campos de Fila
    posicao: int = Field(index=True) 
    tipo_atendimento: str = Field(max_length=1, index=True) # 'N' ou 'P'
    
    # Campos de Status
    atendido: bool = Field(default=False)

# Esquema para criação (usado no POST)
class ClienteCreate(SQLModel):
    nome: str = Field(max_length=20)
    tipo_atendimento: str = Field(max_length=1)

# Esquema para leitura (usado nos GET/PUT)
class ClienteRead(SQLModel):
    nome: str
    tipo_atendimento: str
    id: int
    posicao: int
    data_chegada: datetime
    atendido: bool