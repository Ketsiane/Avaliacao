from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.models import Produto
from app.schemas import ProdutoCreate, ProdutoRead
from app.database import get_session

# Define o prefixo e as tags para agrupar endpoints
router = APIRouter(prefix="/produto", tags=["Produtos"])

@router.post("/", response_model=ProdutoRead, status_code=status.HTTP_201_CREATED)
def cadastrar(produto: ProdutoCreate, session: Session = Depends(get_session)):
    # CORREÇÃO: Utilizando model_validate() para criar a instância do modelo SQLModel a partir do schema Pydantic
    novo_produto = Produto.model_validate(produto) 
    
    session.add(novo_produto)
    session.commit()
    session.refresh(novo_produto) # Atualiza o objeto para incluir o ID gerado pelo banco
    return novo_produto

@router.get("/", response_model=list[ProdutoRead])
def listar(session: Session = Depends(get_session)):
    # Seleciona e retorna todos os produtos
    produtos = session.exec(select(Produto)).all()
    return produtos

@router.get("/{id}", response_model=ProdutoRead)
def recuperar(id: int, session: Session = Depends(get_session)):
    # Busca um produto pelo ID
    produto = session.get(Produto, id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.delete("/{id}")
def deletar(id: int, session: Session = Depends(get_session)):
    # Deleta um produto pelo ID
    produto = session.get(Produto, id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    session.delete(produto)
    session.commit()
    return {"mensagem": "Produto removido com sucesso!"}