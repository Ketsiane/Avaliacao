from datetime import datetime, timezone
from typing import Annotated, List, Union, Tuple, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from app.database import get_session
from app.models import Cliente
from app.schemas import ClienteCreate, ClienteRead, ClienteUpdate 

router = APIRouter(prefix="/fila", tags=["fila"])

# --- Funções Auxiliares de Fila ---

def update_positions(session: Session, start_pos: int, delta: int):
    """Atualiza a posição de todos os clientes não atendidos a partir de uma posição inicial."""
    
    clientes_para_atualizar = session.exec(
        select(Cliente)
        .where(Cliente.atendido == False, Cliente.posicao >= start_pos)
    ).all()
    
    for cliente in clientes_para_atualizar:
        cliente.posicao += delta
        session.add(cliente)
    
    session.commit()

# --- Endpoints ---

@router.delete("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_fila(session: Session = Depends(get_session)):
    """
    Limpa a fila marcando TODOS os clientes (atendidos ou não) como atendidos.
    Usado para iniciar um novo dia ou testes.
    """
    # Seleciona todos os clientes
    clientes = session.exec(select(Cliente)).all()

    # Atualiza o status de todos os clientes para 'atendido'
    for cliente in clientes:
        cliente.atendido = True
        session.add(cliente)

    session.commit()
    return


@router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
def adicionar_cliente(cliente_data: ClienteCreate, session: Session = Depends(get_session)):
    """Adiciona um novo cliente com lógica de prioridade."""
    
    tipo = cliente_data.tipo_atendimento 
    
    # 1. BUSCA DA POSIÇÃO MÁXIMA TOTAL
    # O resultado pode ser um escalar (int ou None) ou uma tupla (int/None,).
    
    resultado_total_row: Union[Tuple[Optional[int]], Optional[int]] = session.exec(
        select(func.max(Cliente.posicao))
        .where(Cliente.atendido == False)
    ).first()
    
    # Lógica robusta para lidar com a diferença entre retorno de escalar ou tupla.
    if resultado_total_row is None:
        # Fila está completamente vazia (None).
        ultima_pos_total = 0
    elif isinstance(resultado_total_row, tuple):
        # Comportamento padrão: retorna uma tupla (max_pos,). Pega o primeiro elemento.
        ultima_pos_total = resultado_total_row[0] or 0
    else:
        # Comportamento desempacotado: retorna um escalar (int).
        ultima_pos_total = resultado_total_row or 0
    
    
    if tipo == 'N':
        # Cliente Normal: vai para o final.
        nova_posicao = ultima_pos_total + 1
    
    elif tipo == 'P':
        # Encontra a posição do último cliente Prioritário ('P')
        resultado_P_row: Union[Tuple[Optional[int]], Optional[int]] = session.exec(
            select(func.max(Cliente.posicao))
            .where(Cliente.atendido == False, Cliente.tipo_atendimento == 'P')
        ).first()

        # Lógica robusta para P:
        if resultado_P_row is None:
            ultima_pos_P = 0
        elif isinstance(resultado_P_row, tuple):
            ultima_pos_P = resultado_P_row[0] or 0
        else:
            ultima_pos_P = resultado_P_row or 0
        
        # Lógica de Prioridade:
        if ultima_pos_P > 0:
            # Entra depois do último P
            nova_posicao = ultima_pos_P + 1
        else:
            # Não há prioritários anteriores. Entra na Posição 1.
            nova_posicao = 1
        
        # Desloca todos (N e P) que estão em ou após nova_posicao em +1.
        if ultima_pos_total >= nova_posicao:
            update_positions(session, nova_posicao, 1)


    # 2. Criação e Inserção do Cliente
    novo_cliente = Cliente.model_validate(cliente_data.model_dump() | {
        'posicao': nova_posicao, 
        'data_chegada': datetime.now(timezone.utc)
    })
    
    session.add(novo_cliente)
    session.commit()
    session.refresh(novo_cliente)
    
    return novo_cliente


@router.get("/", response_model=List[ClienteRead])
def listar_fila(session: Session = Depends(get_session)):
    """Lista todos os clientes na fila (não atendidos), ordenados pela posição."""
    clientes = session.exec(
        select(Cliente)
        .where(Cliente.atendido == False)
        .order_by(Cliente.posicao)
    ).all()
    return clientes


# Adicionado: GET /fila/{posicao} (Busca por Posição)
@router.get("/{posicao}", response_model=ClienteRead)
def buscar_cliente_por_posicao(posicao: int, session: Session = Depends(get_session)):
    """
    Retorna os dados do cliente na posição especificada na fila ativa.
    Retorna 404 se a posição não for válida ou estiver vazia.
    """
    cliente = session.exec(
        select(Cliente)
        .where(Cliente.atendido == False, Cliente.posicao == posicao)
    ).first()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Não há cliente na posição {posicao} da fila."
        )
    
    return cliente


@router.put("/", response_model=ClienteRead)
def atender_proximo_cliente(session: Session = Depends(get_session)):
    """Atende o primeiro cliente da fila e remove-o, deslocando os demais."""
    
    # 1. Encontra o primeiro cliente (posicao = 1)
    cliente_a_atender = session.exec(
        select(Cliente)
        .where(Cliente.posicao == 1, Cliente.atendido == False)
    ).first()
    
    if not cliente_a_atender:
        raise HTTPException(status_code=404, detail="A fila está vazia.")
    
    # 2. Atualiza o status
    cliente_a_atender.atendido = True
    session.add(cliente_a_atender)
    session.commit()
    session.refresh(cliente_a_atender)
    
    # 3. Desloca a fila: subtrai 1 da posição de todos os clientes a partir da posição 2
    update_positions(session, 2, -1)
    
    return cliente_a_atender


@router.delete("/{posicao}", response_model=ClienteRead)
def remover_cliente(posicao: int, session: Session = Depends(get_session)):
    """Remove um cliente específico da fila e desloca os seguintes."""
    
    # 1. Encontra o cliente na posição dada
    cliente_a_remover = session.exec(
        select(Cliente)
        .where(Cliente.posicao == posicao, Cliente.atendido == False)
    ).first()
    
    if not cliente_a_remover:
        raise HTTPException(status_code=404, detail="Cliente não encontrado nesta posição da fila.")
        
    # 2. Remove o cliente (marcando como atendido para fins de histórico e exclusão lógica)
    cliente_a_remover.atendido = True
    session.add(cliente_a_remover)
    session.commit()
    session.refresh(cliente_a_remover)
    
    # 3. Desloca a fila: subtrai 1 da posição de todos os clientes que estavam atrás dele (posicao + 1)
    update_positions(session, posicao + 1, -1)
    
    return cliente_a_remover