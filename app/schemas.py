from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# Esquema para criar um novo cliente (entrada de dados no POST)
class ClienteCreate(BaseModel):
    """
    Schema para criação de um novo cliente na fila.
    Só exige o nome e o tipo de atendimento.
    """
    nome: str
    
    # Restringe o tipo de atendimento a 'N' (Normal) ou 'P' (Prioritário)
    tipo_atendimento: Literal['N', 'P'] = Field(
        default='N', 
        description="Tipo de atendimento: 'N' para Normal, 'P' para Prioritário."
    )

# Esquema para leitura/resposta de um cliente (saída de dados)
class ClienteRead(BaseModel):
    """
    Schema para retornar os dados de um cliente.
    Inclui todos os campos do modelo de banco de dados.
    """
    id: int
    nome: str
    data_chegada: datetime
    posicao: int
    tipo_atendimento: Literal['N', 'P']
    atendido: bool

    class Config:
        # Permite que o Pydantic mapeie os campos do SQLModel (que são orm_mode)
        from_attributes = True

# Inclusão por boas práticas
class ClienteUpdate(BaseModel):
    """
    Schema para atualizar campos de um cliente, todos opcionais.
    """
    nome: Optional[str] = None
    posicao: Optional[int] = None
    tipo_atendimento: Optional[Literal['N', 'P']] = None
    atendido: Optional[bool] = None