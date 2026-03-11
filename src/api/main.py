"""
API FastAPI para o sistema 3D&T completo.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.rag.hybrid_retriever import HybridRetriever
from src.generation.content_generator import ContentGenerator
from src.session.campaign_manager import CampaignSession


app = FastAPI(
    title="3D&T RAG API",
    description="API completa para consulta e geração de conteúdo 3D&T",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instâncias globais (em produção, usar dependency injection)
retriever = HybridRetriever()
generator = ContentGenerator(retriever)
active_sessions: Dict[str, CampaignSession] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    query: str
    top_k: int = 10
    include_visuals: bool = False


class QueryResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    sources_used: List[str]
    timestamp: str


class NPCRequest(BaseModel):
    nivel: int = 1
    arquetipo: Optional[str] = None
    raca: Optional[str] = None


class NPCResponse(BaseModel):
    npc: Dict[str, Any]
    generated_at: str


class EncounterRequest(BaseModel):
    party_size: int = 4
    party_level: int = 1
    dificuldade: str = "medio"
    ambiente: Optional[str] = None


class EncounterResponse(BaseModel):
    encounter: Dict[str, Any]
    xp_total: int
    dificuldade: str


class CombatAction(BaseModel):
    personagem: str
    acao: str
    alvo: Optional[str] = None


class CreateSessionRequest(BaseModel):
    nome: str = Field(default="Aventura", description="Nome da aventura")


class AddCharacterRequest(BaseModel):
    nome: str
    jogador: str
    raca: str
    nivel: int
    stats: Dict[str, int] = Field(default_factory=dict)


class IniciarCombateRequest(BaseModel):
    inimigos: List[Dict[str, Any]] = Field(default_factory=list)


class CompareRequest(BaseModel):
    entidade1: str
    entidade2: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "message": "3D&T RAG API",
        "version": "2.0.0",
        "endpoints": [
            "/query - Consulta híbrida",
            "/npc/gerar - Gerar NPC",
            "/encontro/gerar - Gerar encontro",
            "/sessao/criar - Criar sessão",
            "/sessao/{session_id} - Ver sessão",
            "/sessao/{session_id}/personagem - Adicionar personagem",
            "/combate/{session_id}/iniciar - Iniciar combate",
            "/combate/{session_id}/acao - Executar ação",
            "/regras/buscar - Buscar regras",
            "/entidade/{nome} - Dados de entidade",
            "/comparar - Comparar entidades",
            "/health - Health check",
        ],
    }


@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest) -> QueryResponse:
    """Consulta híbrida: busca em textos + tabelas + raciocínio."""
    try:
        results = retriever.query(request.query, top_k=request.top_k)
        formatted: List[Dict[str, Any]] = []
        sources: set = set()

        for r in results:
            formatted.append({
                "content": r.content,
                "source": r.source,
                "score": r.score,
                "entity": r.entity_name,
                "metadata": r.metadata,
            })
            sources.add(r.source)

        return QueryResponse(
            query=request.query,
            results=formatted,
            sources_used=list(sources),
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/npc/gerar", response_model=NPCResponse)
def generate_npc(request: NPCRequest) -> NPCResponse:
    """Gera NPC balanceado seguindo regras do 3D&T."""
    try:
        npc = generator.generate_npc(
            nivel=request.nivel,
            arquetipo=request.arquetipo,
            raca=request.raca,
        )
        return NPCResponse(
            npc=npc.to_dict(),
            generated_at=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/encontro/gerar", response_model=EncounterResponse)
def generate_encounter(request: EncounterRequest) -> EncounterResponse:
    """Gera encontro balanceado para a party."""
    try:
        encounter = generator.generate_encounter(
            party_size=request.party_size,
            party_level=request.party_level,
            dificuldade=request.dificuldade,
            ambiente=request.ambiente,
        )
        return EncounterResponse(
            encounter=encounter,
            xp_total=encounter.get("xp_total", 0),
            dificuldade=request.dificuldade,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessao/criar")
def create_session(body: CreateSessionRequest) -> Dict[str, Any]:
    """Cria nova sessão de campanha."""
    session = CampaignSession(nome=body.nome)
    session.save()
    active_sessions[session.session_id] = session
    return {
        "session_id": session.session_id,
        "nome": body.nome,
        "created_at": session.created_at,
        "url": f"/sessao/{session.session_id}",
    }


@app.get("/sessao/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    """Recupera estado da sessão."""
    if session_id not in active_sessions:
        session = CampaignSession.load(session_id)
        if session:
            active_sessions[session_id] = session
        else:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")

    session = active_sessions[session_id]
    return {
        "session_id": session_id,
        "nome": session.nome,
        "personagens": [p.to_dict() for p in session.player_characters],
        "combate_ativo": session.combate_ativo.to_dict() if session.combate_ativo else None,
        "historia_count": len(session.historia),
    }


@app.post("/sessao/{session_id}/personagem")
def add_character(session_id: str, body: AddCharacterRequest) -> Dict[str, Any]:
    """Adiciona personagem à sessão."""
    if session_id not in active_sessions:
        session = CampaignSession.load(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        active_sessions[session_id] = session

    session = active_sessions[session_id]
    pc = session.add_player_character(
        nome=body.nome,
        jogador=body.jogador,
        raca=body.raca,
        nivel=body.nivel,
        stats=body.stats or {},
    )
    return {"status": "ok", "personagem": pc.to_dict()}


@app.post("/combate/{session_id}/iniciar")
def iniciar_combate(session_id: str, body: IniciarCombateRequest) -> Dict[str, Any]:
    """Inicia combate na sessão."""
    if session_id not in active_sessions:
        session = CampaignSession.load(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        active_sessions[session_id] = session

    session = active_sessions[session_id]
    status = session.iniciar_combate(body.inimigos or [])
    return {
        "status": "combate_iniciado",
        "resumo": status,
        "rodada": 1,
    }


@app.post("/combate/{session_id}/acao")
def executar_acao(session_id: str, action: CombatAction) -> Dict[str, Any]:
    """Executa ação no combate."""
    if session_id not in active_sessions:
        session = CampaignSession.load(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        active_sessions[session_id] = session

    session = active_sessions[session_id]
    return session.executar_acao(
        action.personagem,
        action.acao,
        action.alvo,
    )


@app.get("/regras/buscar")
def buscar_regra(q: str) -> Dict[str, Any]:
    """Busca rápida em regras."""
    results = retriever.query(q, top_k=5)
    return {
        "query": q,
        "regras_encontradas": [
            {
                "texto": r.content[:300],
                "fonte": r.source,
                "confianca": r.score,
            }
            for r in results
        ],
    }


@app.get("/entidade/{nome}")
def get_entity(nome: str) -> Dict[str, Any]:
    """Recupera dados completos de uma entidade (monstro, magia, etc.)."""
    data = retriever._get_entity_data(nome)
    if not data:
        raise HTTPException(status_code=404, detail="Entidade não encontrada")
    return {
        "nome": nome,
        "dados": data.get("structured_data", {}),
        "tipo": data.get("table_type", "unknown"),
        "fonte": data.get("source", "unknown"),
    }


@app.post("/comparar")
def comparar_entidades(body: CompareRequest) -> Dict[str, Any]:
    """Compara duas entidades."""
    comparison = retriever.compare_entities(body.entidade1, body.entidade2)
    if not comparison:
        raise HTTPException(
            status_code=404,
            detail="Uma ou ambas entidades não encontradas",
        )
    return comparison


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "components": {
            "retriever": "loaded",
            "generator": "loaded",
            "active_sessions": len(active_sessions),
        },
    }


def start_api(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Inicia servidor API."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_api()
