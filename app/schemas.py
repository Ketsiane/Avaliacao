from sqlmodel import SQLModel
from typing import Optional
# Importação necessária para a correção do orm_mode
from pydantic import ConfigDict 

# Schema para criação: herda de SQLModel (em vez de BaseModel)
class ProdutoCreate(SQLModel):
    nome: str
    preco: float
    descricao: Optional[str] = None

# Schema para leitura: inclui o ID gerado pelo banco
class ProdutoRead(ProdutoCreate):
    id: int
    
    # Substitui 'orm_mode = True' para compatibilidade com Pydantic v2
    model_config = ConfigDict(from_attributes=True)