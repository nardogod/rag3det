# app.py - Interface Web do Mestre Autonomo 3D&T
"""
Interface Streamlit: Jogador (multipla escolha) e Modo Mestre (chat sobre os livros).
Executar:  python -m streamlit run app.py
"""

import streamlit as st
from src.master.master_autonomo_3dt import MestreAutonomo3DT, EstiloNarrativo

st.set_page_config(
    page_title="3D&T Mestre Autonomo",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estado da sessao
if "mestre" not in st.session_state:
    st.session_state.mestre = None
if "historico" not in st.session_state:
    st.session_state.historico = []
if "ultima_narracao" not in st.session_state:
    st.session_state.ultima_narracao = ""
if "ultima_decisao" not in st.session_state:
    st.session_state.ultima_decisao = None
if "sistema_consulta" not in st.session_state:
    st.session_state.sistema_consulta = None
if "chat_mestre" not in st.session_state:
    st.session_state.chat_mestre = []
if "use_llm_narracao" not in st.session_state:
    st.session_state.use_llm_narracao = False
if "modo_debug" not in st.session_state:
    st.session_state.modo_debug = False


def renderizar_resposta_mestre(decisao) -> None:
    """Renderiza a resposta estruturada do mestre (teste, narracao, mudancas de estado)."""
    with st.container(border=True):
        # Cabecalho do teste
        teste = getattr(decisao, "teste_necessario", None)
        if teste:
            st.subheader(f"Teste de {teste.atributo}")
            cols = st.columns(4)
            cols[0].metric("Classe de Dificuldade", teste.cd)
            cols[1].metric("Resultado", teste.resultado or "-")
            cols[2].metric("Sucesso", "Sim" if teste.sucesso else "Nao")
            cols[3].metric("Descricao", teste.descricao[:40] + "..." if len((teste.descricao or "")) > 40 else (teste.descricao or "-"))
            if teste.descricao:
                st.caption(teste.descricao)

        # Narracao
        st.markdown("### Narracao")
        conteudo = decisao.conteudo or getattr(decisao, "resultado_acao", "") or ""
        st.write(conteudo)

        # Mudancas de estado
        mudanca = getattr(decisao, "mudanca_estado", None) or {}
        descobertas = mudanca.get("descobertas_add", [])
        inimigos = mudanca.get("inimigos_add", [])
        objetivos = mudanca.get("objetivos_add", [])
        em_combate = mudanca.get("em_combate")

        if descobertas or inimigos or objetivos or em_combate is not None:
            st.markdown("### Mudancas no Estado")
            if descobertas:
                for d in descobertas:
                    st.success(f"Descoberta: {d}")
            if inimigos:
                for i in inimigos:
                    st.warning(f"Inimigo: {i}")
            if objetivos:
                for o in objetivos:
                    st.info(f"Objetivo: {o}")
            if em_combate is True:
                st.error("COMBATE INICIADO!")


def inferir_intencao(acao: str) -> str:
    """Inferir intencao da acao do jogador."""
    if not acao or not acao.strip():
        return "explorar"
    a = acao.lower().strip()
    if any(x in a for x in ["atacar", "combate", "lutar", "golpear"]):
        return "atacar"
    if any(x in a for x in ["falar", "persuadir", "convencer", "negociar", "perguntar"]):
        return "falar"
    if any(x in a for x in [
        "investigar", "procurar", "buscar", "olhar", "explorar",
        "sigo", "avancar", "caminho", "entrar", "andando", "em frente", "deslocar",
        "runas", "paredes", "corredor", "armadilhas", "detalhes",
    ]):
        return "investigar"
    return "explorar"


def iniciar_campanha(estilo: str, sessoes: int, party_size: int, nivel: int, tema: str) -> None:
    with st.spinner("Mestre esta criando o mundo..."):
        mestre = MestreAutonomo3DT(
            estilo=EstiloNarrativo[estilo],
            duracao_prevista=sessoes,
        )
        mestre.use_llm_narracao = st.session_state.use_llm_narracao
        resultado = mestre.criar_campanha_autonoma(
            tema=tema,
            party_size=party_size,
            nivel_inicial=nivel,
        )
        mestre.preparar_sessao(1)
        sessao_info = mestre.iniciar_sessao_autonoma(1)
        intro = sessao_info.get("introducao", "")
        st.session_state.mestre = mestre
        st.session_state.historico = [
            f"**Campanha criada:** {resultado['titulo']}",
            "---",
            "**Mestre (introducao):**",
            intro,
        ]
        st.session_state.ultima_narracao = intro
        st.session_state.ultima_decisao = None


def get_sistema_consulta():
    """Lazy init do sistema para consultas (Modo Mestre)."""
    if st.session_state.sistema_consulta is None:
        with st.spinner("Carregando sistema de consulta aos livros..."):
            from src.integration.sistema_multimodal_3dt import SistemaMultimodal3DT
            st.session_state.sistema_consulta = SistemaMultimodal3DT()
    return st.session_state.sistema_consulta


def _llm_label():
    """Texto do radio para LLM (Ollama ou OpenAI conforme config)."""
    try:
        from src.config import llm_config
        p = (llm_config.provider or "ollama").lower()
        if p == "ollama":
            return f"LLM (Ollama: {getattr(llm_config, 'ollama_model', 'llama3.1')})"
        if p == "openai":
            return f"LLM (OpenAI: {getattr(llm_config, 'openai_model_name', 'gpt-4')})"
        return "LLM (modelo configurado)"
    except Exception:
        return "LLM (Ollama/OpenAI)"


def testar_ollama():
    """Testa conexao com Ollama e retorna (ok, mensagem)."""
    try:
        from src.generation.llm_provider import get_chat_llm
        llm = get_chat_llm()
        # Chamada leve para ver se responde
        from langchain_core.messages import HumanMessage
        r = llm.invoke([HumanMessage(content="Diga apenas: OK")])
        if r and (getattr(r, "content", "") or str(r)):
            return True, "Conexao com Ollama OK. Narracao sera gerada pelo LLM."
        return False, "Ollama respondeu vazio."
    except Exception as e:
        return False, f"Erro: {e}. Verifique se o Ollama esta rodando (ollama serve) e o modelo baixado (ollama pull <modelo>)."


# Sidebar
with st.sidebar:
    st.header("Configuracao da Campanha")
    estilo = st.selectbox(
        "Estilo",
        ["HEROICO", "EPICO", "SOMBRIO", "INTRIGA", "EXPLORACAO"],
    )
    sessoes = st.slider("Duracao (sessoes)", 2, 10, 3)
    party_size = st.number_input("Jogadores", 2, 6, 4)
    nivel = st.number_input("Nivel inicial", 1, 5, 1)
    tema = st.text_area(
        "Tema/Conceito",
        "Uma antiga masmorra ressurge, trazendo monstros que ameacam a vila.",
    )
    if st.button("Criar Campanha", type="primary"):
        iniciar_campanha(estilo, sessoes, party_size, nivel, tema)

    st.divider()
    st.subheader("Narracao do Mestre")
    opcao_sistema = "Sistema (regras e cenas preparadas)"
    opcao_llm = _llm_label()
    modo_narracao = st.radio(
        "Quem gera a narracao?",
        [opcao_sistema, opcao_llm],
        index=1 if st.session_state.use_llm_narracao else 0,
    )
    use_llm = opcao_llm == modo_narracao
    st.session_state.use_llm_narracao = use_llm
    if st.session_state.mestre is not None:
        st.session_state.mestre.use_llm_narracao = use_llm
    if use_llm:
        st.caption("Ollama: rode `ollama serve` e baixe o modelo com `ollama pull llama3.1` (ou o modelo do .env).")
        if st.button("Testar conexao Ollama"):
            ok, msg = testar_ollama()
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.divider()
    st.subheader("Estado Atual")
    if st.session_state.mestre and st.session_state.mestre.estado_cena_atual:
        estado = st.session_state.mestre.estado_cena_atual
        from src.master.master_autonomo_3dt import EstadoCena, TesteRPG  # type: ignore

        estado_dict = {
            "Local": estado.nome,
            "Descricao": estado.descricao,
            "Descobertas": list(estado.descobertas),
            "Inimigos_Visiveis": list(estado.inimigos_visiveis),
            "Objetivos": list(estado.objetivos),
            "Em_Combate": estado.em_combate,
        }
        if estado.ultimo_teste:
            estado_dict["Ultimo_Teste"] = {
                "Atributo": estado.ultimo_teste.atributo,
                "Classe de Dificuldade": estado.ultimo_teste.cd,
                "Resultado": estado.ultimo_teste.resultado,
                "Sucesso": estado.ultimo_teste.sucesso,
                "Descricao": estado.ultimo_teste.descricao,
            }
        st.json(estado_dict)
        if estado.em_combate:
            st.warning("COMBATE EM ANDAMENTO")

    st.divider()
    modo_debug = st.checkbox("Modo Debug", value=st.session_state.modo_debug, key="modo_debug_cb")
    st.session_state.modo_debug = modo_debug
    if modo_debug:
        st.subheader("Schema do Mestre (Raw)")
        if st.session_state.ultima_decisao:
            dec = st.session_state.ultima_decisao
            debug_dict = {
                "tipo": dec.tipo,
                "conteudo": (dec.conteudo or "")[:200],
                "teste_necessario": (
                    {
                        "atributo": dec.teste_necessario.atributo,
                        "cd": dec.teste_necessario.cd,
                        "resultado": dec.teste_necessario.resultado,
                        "sucesso": dec.teste_necessario.sucesso,
                    }
                    if dec.teste_necessario
                    else None
                ),
                "mudanca_estado": getattr(dec, "mudanca_estado", {}),
                "opcoes_jogador": getattr(dec, "opcoes_jogador", []),
            }
            st.json(debug_dict)
        else:
            st.caption("Nenhuma decisao ainda.")

# Tabs principais
tab_jogador, tab_mestre = st.tabs(["Jogador", "Modo Mestre"])

# --- ABA JOGADOR: multipla escolha ---
with tab_jogador:
    if st.session_state.mestre:
        mestre = st.session_state.mestre

        col1, col2, col3 = st.columns(3)
        col1.metric("Fase", mestre.fase.name)
        sessao_atual = mestre.sistema.campanha.sessao_atual
        col2.metric("Sessao", str(sessao_atual.numero) if sessao_atual else "0")
        col3.metric("Cena", str(mestre.cena_atual + 1))

        st.subheader("Narracao do Mestre")
        decisao = st.session_state.ultima_decisao
        if decisao:
            renderizar_resposta_mestre(decisao)
        elif st.session_state.ultima_narracao:
            st.markdown(st.session_state.ultima_narracao)
        else:
            st.info("Escolha uma acao abaixo para continuar.")

        st.subheader("Suas Acoes")
        decisao = st.session_state.ultima_decisao  # reutiliza para opcoes
        opcoes = getattr(decisao, "opcoes_jogador", None) if decisao else None
        pcs = [
            p.nome for p in mestre.sistema.campanha.personagens.values()
            if getattr(p, "tipo", "") == "pc"
        ]
        if not pcs:
            pcs = ["Thorin", "Lyra", "Outro"]
        personagem = st.selectbox("Personagem", pcs + ["Novo Personagem..."], key="personagem_jogador")

        # Multipla escolha: botoes com as opcoes da ultima decisao
        if opcoes and len(opcoes) >= 2:
            acao_escolhida = None
            for i, opt in enumerate(opcoes):
                if st.button(opt, key=f"opt_{i}"):
                    acao_escolhida = opt
                    break
            if acao_escolhida is not None:
                with st.spinner("Mestre esta pensando..."):
                    intencao = inferir_intencao(acao_escolhida)
                    dec = mestre.processar_acao_jogadores([
                        {
                            "jogador": "user",
                            "personagem": personagem if personagem != "Novo Personagem..." else "Aventureiro",
                            "acao_descricao": acao_escolhida,
                            "intencao": intencao,
                        }
                    ])
                    st.session_state.historico.append(f"**Voce ({personagem}):** {acao_escolhida}")
                    st.session_state.historico.append(f"**Mestre:** {dec.conteudo}")
                    st.session_state.ultima_narracao = dec.conteudo
                    st.session_state.ultima_decisao = dec
                st.rerun()
        else:
            # Primeira tela ou sem opcoes: mostrar introducao e opcoes genericas
            opcoes_inicio = [
                "Olhar em volta e descrever o ambiente",
                "Seguir em frente com cuidado",
                "Investigar as runas nas paredes",
                "Procurar armadilhas",
                "Falar com o grupo",
            ]
            for i, opt in enumerate(opcoes_inicio):
                if st.button(opt, key=f"opt_inicio_{i}"):
                    with st.spinner("Mestre esta pensando..."):
                        intencao = inferir_intencao(opt)
                        dec = mestre.processar_acao_jogadores([
                            {
                                "jogador": "user",
                                "personagem": personagem if personagem != "Novo Personagem..." else "Aventureiro",
                                "acao_descricao": opt,
                                "intencao": intencao,
                            }
                        ])
                        st.session_state.historico.append(f"**Voce ({personagem}):** {opt}")
                        st.session_state.historico.append(f"**Mestre:** {dec.conteudo}")
                        st.session_state.ultima_narracao = dec.conteudo
                        st.session_state.ultima_decisao = dec
                    st.rerun()

        with st.expander("Historico da Sessao"):
            for msg in reversed(st.session_state.historico[-20:]):
                st.markdown(msg)
    else:
        st.info(
            "Configure a campanha no menu lateral e clique em **Criar Campanha**. "
            "Depois use as opcoes na tela para jogar."
        )

# --- ABA MODO MESTRE: chat sobre o universo / livros ---
with tab_mestre:
    st.subheader("Modo Mestre")
    st.markdown(
        "Pergunte qualquer coisa sobre o **universo e as regras de 3D&T**. "
        "O sistema busca nos livros e materiais indexados e responde com base no conteudo."
    )
    for msg in st.session_state.chat_mestre:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if prompt := st.chat_input("Ex.: Como funciona iniciativa? Quanto XP um goblin da?"):
        st.session_state.chat_mestre.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                sistema = get_sistema_consulta()
                resposta = sistema.consultar(prompt, incluir_visuais=False)
                texto = resposta.intencao or ""
                if resposta.dados_recuperados:
                    texto += "\n\n**Referencias:**\n"
                    for d in resposta.dados_recuperados[:5]:
                        fonte = d.get("fonte", d.get("tipo", "?"))
                        trecho = (d.get("conteudo") or d.get("text", ""))[:300]
                        if trecho:
                            texto += f"\n- *{fonte}*: {trecho}...\n"
                if resposta.conteudo_gerado:
                    cg = resposta.conteudo_gerado
                    if isinstance(cg, dict) and cg.get("encontro"):
                        enc = cg["encontro"]
                        texto += f"\n\n**Encontro:** {enc.get('nome', '')} - {enc.get('descricao', '')[:200]}..."
                    elif isinstance(cg, dict):
                        texto += "\n\n" + str(cg)[:500]
                if not texto.strip():
                    texto = "Nenhum resultado encontrado nos materiais indexados."
                st.markdown(texto)
                st.session_state.chat_mestre.append({"role": "assistant", "content": texto})
            except Exception as e:
                st.error(f"Erro ao consultar: {e}")
                st.session_state.chat_mestre.append({"role": "assistant", "content": f"Erro: {e}"})
