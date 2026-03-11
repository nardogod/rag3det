"""
NIVEL 7.5: INTEGRACAO MULTIMODAL COMPLETA
Integra processamento visual ao sistema 3D&T unificado.
Permite consultas combinando texto + imagens.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.multimedia.visual_system_3dt import (
    ElementoVisual,
    FichaOCR,
    MapaProcessado,
    TipoVisual,
    VisualProcessor3DT,
)
from src.rag.sistema_completo_3dt import Resposta3DT, Sistema3DT


class TipoConsultaVisual(Enum):
    """Tipos de consulta que envolvem elementos visuais."""
    BUSCA_IMAGEM_ENTIDADE = "busca_imagem_entidade"
    DESCRICAO_MAPA = "descricao_mapa"
    OCR_FICHA = "ocr_ficha"
    COMPARACAO_VISUAL = "comparacao_visual"
    GERACAO_COM_REFERENCIA = "geracao_com_referencia"
    ANALISE_TATICA = "analise_tatica"


@dataclass
class ContextoVisual:
    """Contexto visual para enriquecer respostas."""
    imagens_referenciadas: List[ElementoVisual] = field(default_factory=list)
    mapas_ativos: List[MapaProcessado] = field(default_factory=list)
    fichas_ocr: List[FichaOCR] = field(default_factory=list)
    descricoes_geradas: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "imagens": [img.to_dict() for img in self.imagens_referenciadas],
            "mapas": [
                {
                    "id": m.id,
                    "nome": m.nome,
                    "tipo": m.tipo.value,
                    "dimensoes_pixels": list(m.dimensoes_pixels),
                    "escala": m.escala,
                    "pontos_interesse": m.pontos_interesse,
                    "conexoes": m.conexoes,
                    "areas_perigosas": m.areas_perigosas,
                    "notas_mestre": m.notas_mestre,
                    "imagem_path": str(m.imagem_path),
                }
                for m in self.mapas_ativos
            ],
            "fichas": [f.to_dict() for f in self.fichas_ocr],
            "descricoes": self.descricoes_geradas,
        }


@dataclass
class RespostaMultimodal(Resposta3DT):
    """Resposta estendida com componentes visuais."""
    contexto_visual: Optional[ContextoVisual] = None
    tipo_consulta_visual: Optional[TipoConsultaVisual] = None
    imagens_para_exibir: List[Dict[str, Any]] = field(default_factory=list)
    acoes_visuais_sugeridas: List[str] = field(default_factory=list)

    def tem_conteudo_visual(self) -> bool:
        return (
            self.contexto_visual is not None
            and (
                bool(self.contexto_visual.imagens_referenciadas)
                or bool(self.contexto_visual.mapas_ativos)
            )
        )

    def gerar_resposta_texto(self) -> str:
        """Gera resposta textual rica incluindo descricoes visuais."""
        linhas: List[str] = []
        if self.contexto_visual and self.contexto_visual.descricoes_geradas:
            linhas.extend(self.contexto_visual.descricoes_geradas)
        if self.contexto_visual and self.contexto_visual.mapas_ativos:
            for mapa in self.contexto_visual.mapas_ativos:
                linhas.append(f"\n[MAPA] {mapa.nome}:")
                linhas.append(mapa.gerar_descricao_textual())
        return "\n".join(linhas) if linhas else (self.intencao or "")


class SistemaMultimodal3DT(Sistema3DT):
    """
    Sistema 3D&T completo com capacidades multimodais.
    Herda do Sistema3DT e adiciona processamento visual.
    """

    def __init__(
        self,
        campaign_id: Optional[str] = None,
        campaign_name: str = "Aventura 3D&T",
        visual_output_dir: str = "data/visual",
    ) -> None:
        super().__init__(campaign_id, campaign_name)
        self.visual = VisualProcessor3DT(visual_output_dir)
        self.entity_image_index: Dict[str, List[str]] = {}
        self._construir_indice_visual()
        print("Multimodal: OK")
        total = sum(len(v) for v in self.entity_image_index.values())
        print(f"   Imagens indexadas: {total}")

    def _construir_indice_visual(self) -> None:
        """Constroi indice invertido de entidades para imagens."""
        self.entity_image_index.clear()
        for elem_id, elem in self.visual.elementos.items():
            for entidade in elem.entidades_relacionadas:
                key = entidade.lower()
                self.entity_image_index.setdefault(key, []).append(elem_id)

    def consultar(
        self,
        query: str,
        contexto: Optional[Dict[str, Any]] = None,
        incluir_visuais: bool = True,
    ) -> RespostaMultimodal:
        """
        Consulta multimodal completa.
        Fluxo: Analise -> Busca texto -> Busca/processamento visual -> Integracao.
        """
        print(f"\n{'='*80}")
        print(f"CONSULTA MULTIMODAL: '{query}'")
        print(f"{'='*80}")

        tipo_visual = (
            self._detectar_tipo_consulta_visual(query)
            if incluir_visuais
            else None
        )
        resposta_base = super().consultar(query, contexto)

        if not tipo_visual:
            return RespostaMultimodal(
                query_original=resposta_base.query_original,
                intencao=resposta_base.intencao,
                dados_recuperados=resposta_base.dados_recuperados,
                analise_inteligente=resposta_base.analise_inteligente,
                conteudo_gerado=resposta_base.conteudo_gerado,
                contexto_campanha=resposta_base.contexto_campanha,
                sugestoes=resposta_base.sugestoes,
                proximos_passos=resposta_base.proximos_passos,
                contexto_visual=None,
                tipo_consulta_visual=None,
            )

        contexto_visual = self._processar_componente_visual(
            tipo_visual, query, resposta_base
        )
        sugestoes_visuais = self._gerar_sugestoes_visuais(
            tipo_visual, contexto_visual
        )
        imagens_exibir = self._preparar_imagens_display(contexto_visual)

        resposta = RespostaMultimodal(
            query_original=resposta_base.query_original,
            intencao=resposta_base.intencao,
            dados_recuperados=resposta_base.dados_recuperados,
            analise_inteligente=resposta_base.analise_inteligente,
            conteudo_gerado=resposta_base.conteudo_gerado,
            contexto_campanha=resposta_base.contexto_campanha,
            sugestoes=list(set(resposta_base.sugestoes + sugestoes_visuais)),
            proximos_passos=resposta_base.proximos_passos,
            contexto_visual=contexto_visual,
            tipo_consulta_visual=tipo_visual,
            imagens_para_exibir=imagens_exibir,
            acoes_visuais_sugeridas=sugestoes_visuais,
        )

        self.campanha.registrar_evento(
            f"Consulta multimodal: {query[:50]}...",
            tipo="consulta_visual",
            envolvidos=[],
            importancia=2,
            metadata={
                "tipo_visual": tipo_visual.value,
                "imagens_encontradas": (
                    len(contexto_visual.imagens_referenciadas)
                    if contexto_visual
                    else 0
                ),
            },
        )
        return resposta

    def _detectar_tipo_consulta_visual(
        self, query: str
    ) -> Optional[TipoConsultaVisual]:
        """Detecta se a consulta requer processamento visual."""
        query_lower = query.lower()
        padroes = {
            TipoConsultaVisual.BUSCA_IMAGEM_ENTIDADE: [
                r"mostre.*imagem",
                r"imagem d[eoa]",
                r"foto d[eoa]",
                r"visual d[eoa]",
                r"como.*parece",
                r"aparencia d[eoa]",
                r"look.*like",
            ],
            TipoConsultaVisual.DESCRICAO_MAPA: [
                r"mapa.*descri",
                r"descreva.*mapa",
                r"explique.*mapa",
                r"pontos.*interesse",
                r"como.*chegar",
                r"caminho.*mapa",
            ],
            TipoConsultaVisual.OCR_FICHA: [
                r"extraia.*ficha",
                r"ler.*ficha",
                r"ocr",
                r"dados.*imagem",
                r"informacoes.*ficha",
                r"personagem.*imagem",
            ],
            TipoConsultaVisual.COMPARACAO_VISUAL: [
                r"compare.*imagens",
                r"diferenca.*visual",
                r"parecido com",
                r"similar.*imagem",
            ],
            TipoConsultaVisual.GERACAO_COM_REFERENCIA: [
                r"crie.*parecido",
                r"gerar.*baseado",
                r"inspirado.*imagem",
                r"semelhante.*a",
            ],
            TipoConsultaVisual.ANALISE_TATICA: [
                r"analise.*tatica",
                r"posicao.*combate",
                r"estrategia.*mapa",
                r"vantagem.*terreno",
            ],
        }
        for tipo, padroes_lista in padroes.items():
            for padrao in padroes_lista:
                if re.search(padrao, query_lower):
                    print(f"   Detectado tipo visual: {tipo.value}")
                    return tipo
        return None

    def _processar_componente_visual(
        self,
        tipo: TipoConsultaVisual,
        query: str,
        resposta_base: Resposta3DT,
    ) -> ContextoVisual:
        """Processa a parte visual da consulta."""
        contexto = ContextoVisual()
        analise = resposta_base.analise_inteligente or {}

        if tipo == TipoConsultaVisual.BUSCA_IMAGEM_ENTIDADE:
            entidades = analise.get("entidades_principais", [])
            if not entidades:
                entidades = self._extrair_entidade_query(query)
            for entidade in entidades:
                imagens = self.visual.buscar_por_entidade(entidade)
                contexto.imagens_referenciadas.extend(imagens)
                print(f"   [IMG] {entidade}: {len(imagens)} imagem(ns)")
                for img in imagens[:1]:
                    desc = self._gerar_descricao_imagem(img, entidade)
                    contexto.descricoes_geradas.append(desc)

        elif tipo == TipoConsultaVisual.DESCRICAO_MAPA:
            mapas = self._buscar_mapas_query(query)
            contexto.mapas_ativos = mapas
            for mapa in mapas:
                print(
                    f"   [MAP] {mapa.nome} ({len(mapa.pontos_interesse)} POIs)"
                )

        elif tipo == TipoConsultaVisual.OCR_FICHA:
            ficha = self._processar_ficha_upload(query)
            if ficha:
                contexto.fichas_ocr.append(ficha)
                contexto.descricoes_geradas.append(
                    self._formatar_ficha_ocr(ficha)
                )

        elif tipo == TipoConsultaVisual.ANALISE_TATICA:
            mapas = self._buscar_mapas_combate(query)
            for mapa in mapas:
                analise_txt = self._analisar_taticamente(mapa, resposta_base)
                contexto.mapas_ativos.append(mapa)
                contexto.descricoes_geradas.append(analise_txt)

        return contexto

    def _extrair_entidade_query(self, query: str) -> List[str]:
        """Extrai possiveis nomes de entidades da query."""
        analise = self.reasoning.analisar(query)
        return analise.entidades if analise.entidades else ["desconhecido"]

    def _gerar_descricao_imagem(
        self, img: ElementoVisual, entidade: str
    ) -> str:
        """Gera descricao textual de uma imagem para RAG."""
        descricoes = {
            TipoVisual.ILUSTRACAO_MONSTRO: (
                f"[MONSTRO] {entidade.upper()}: Criatura em {img.source} (p. {img.pagina}). "
                f"Ilustracao oficial. Dimensoes: {img.dimensoes[0]}x{img.dimensoes[1]}px. "
                f"Contexto: {(img.contexto_texto or '')[:100]}..."
            ),
            TipoVisual.ILUSTRACAO_PERSONAGEM: (
                f"[PERSONAGEM] {entidade}: Em {img.source}. "
                f"Arte conceitual ({img.dimensoes[0]}x{img.dimensoes[1]}px)."
            ),
            TipoVisual.ILUSTRACAO_EQUIPAMENTO: (
                f"[EQUIP] {entidade}: Equipamento ilustrado. "
                f"Visual disponivel para referencia."
            ),
            TipoVisual.FICHA_PERSONAGEM: (
                f"[FICHA] Ficha de {entidade} em formato visual. "
                f"OCR pode extrair atributos."
            ),
            TipoVisual.MAPA_DUNGEON: (
                f"[MAPA] Mapa de masmorra relacionado a {entidade}. "
                f"Uso para navegacao tactica."
            ),
            TipoVisual.DESCONHECIDO: (
                f"[IMG] Imagem relacionada a {entidade} ({img.tipo.value}). "
                f"Fonte: {img.source} p.{img.pagina}."
            ),
        }
        return descricoes.get(img.tipo, descricoes[TipoVisual.DESCONHECIDO])

    def _buscar_mapas_query(self, query: str) -> List[MapaProcessado]:
        """Busca mapas relacionados a query."""
        resultados: List[MapaProcessado] = []
        termos = query.lower().split()
        for mapa in self.visual.mapas.values():
            if any(t in mapa.nome.lower() for t in termos):
                resultados.append(mapa)
                continue
            for poi in mapa.pontos_interesse:
                desc = (poi.get("descricao") or "").lower()
                if any(t in desc for t in termos):
                    resultados.append(mapa)
                    break
        return resultados[:3]

    def _buscar_mapas_combate(self, query: str) -> List[MapaProcessado]:
        """Busca mapas de combate."""
        elementos = self.visual.listar_por_tipo(TipoVisual.MAPA_COMBATE)
        return [
            self.visual.mapas[m.id]
            for m in elementos
            if m.id in self.visual.mapas
        ]

    def _analisar_taticamente(
        self, mapa: MapaProcessado, resposta_base: Resposta3DT
    ) -> str:
        """Gera analise tactica de um mapa."""
        linhas = [
            f"ANALISE TATICA: {mapa.nome}",
            "=" * 50,
            "",
            "POSICIONAMENTO RECOMENDADO:",
        ]
        for poi in mapa.pontos_interesse:
            desc = (poi.get("descricao") or "").lower()
            if any(x in desc for x in ["alto", "elevado", "torre"]):
                linhas.append(
                    f"  - {poi.get('label', '?')}: VANTAGEM ELEVADA (+2 ataques a distancia)"
                )
            elif any(x in desc for x in ["cobertura", "parede", "rocha"]):
                linhas.append(
                    f"  - {poi.get('label', '?')}: COBERTURA (+2 defesa)"
                )
            elif any(x in desc for x in ["estreito", "ponte", "porta"]):
                linhas.append(
                    f"  - {poi.get('label', '?')}: GARGALO (controle de movimento)"
                )
        if mapa.areas_perigosas:
            linhas.extend(["", "PERIGOS IDENTIFICADOS:"])
            for area in mapa.areas_perigosas:
                linhas.append(
                    f"  - {area.get('nome', '?')}: {area.get('descricao', '')}"
                )
        linhas.extend([
            "",
            "ESTRATEGIA SUGERIDA:",
            "1. Posicione arqueiros em pontos elevados",
            "2. Use gargalos para controlar numero de inimigos",
            "3. Evite areas perigosas sem preparo",
        ])
        return "\n".join(linhas)

    def _processar_ficha_upload(self, query: str) -> Optional[FichaOCR]:
        """Processamento de ficha (cache ou upload futuro)."""
        for ficha in self.visual.fichas_ocr.values():
            if ficha.nome_personagem and (
                ficha.nome_personagem.lower() in query.lower()
            ):
                return ficha
        return None

    def _formatar_ficha_ocr(self, ficha: FichaOCR) -> str:
        """Formata ficha OCR para exibicao."""
        linhas = [
            f"[FICHA] {ficha.nome_personagem or 'Desconhecido'}",
            f"   Jogador: {ficha.nome_jogador or 'N/A'}",
            f"   Raca: {ficha.raca or '?'} | Classe: {ficha.classe or '?'} | Nivel: {ficha.nivel or '?'}",
            "",
            "   ATRIBUTOS:",
        ]
        for attr, val in ficha.atributos.items():
            linhas.append(f"      {attr}: {val if val is not None else '?'}")
        if ficha.pericias:
            linhas.extend([
                "",
                "   PERICIAS:",
                f"      {', '.join(ficha.pericias[:5])}",
            ])
        if ficha.equipamento:
            linhas.extend([
                "",
                "   EQUIPAMENTO:",
                f"      {', '.join(ficha.equipamento[:3])}",
            ])
        conf = ficha.validacao.get("confianca_geral", 0) or 0
        linhas.append(f"\n   Confianca OCR: {conf * 100:.0f}%")
        return "\n".join(linhas)

    def _gerar_sugestoes_visuais(
        self,
        tipo: TipoConsultaVisual,
        contexto: ContextoVisual,
    ) -> List[str]:
        """Gera sugestoes para contextos visuais."""
        sugestoes: List[str] = []
        if tipo == TipoConsultaVisual.BUSCA_IMAGEM_ENTIDADE:
            sugestoes.append("Descreva esta criatura em detalhes")
            sugestoes.append("Compare com outras imagens do bestiario")
            sugestoes.append("Gere encontro usando esta aparencia")
        elif tipo == TipoConsultaVisual.DESCRICAO_MAPA:
            sugestoes.append("Analise tactica deste mapa")
            sugestoes.append("Gere encontro para esta localizacao")
            sugestoes.append("Calcule distancias entre pontos")
        elif tipo == TipoConsultaVisual.OCR_FICHA:
            sugestoes.append("Valide atributos extraidos")
            sugestoes.append("Importe para campanha atual")
            sugestoes.append("Compare com personagens existentes")
        elif contexto.mapas_ativos:
            sugestoes.append("Exportar mapa para VTTRPG")
            sugestoes.append("Adicionar novos pontos de interesse")
        return sugestoes

    def _preparar_imagens_display(
        self, contexto: ContextoVisual
    ) -> List[Dict[str, Any]]:
        """Converte imagens para base64 para exibicao."""
        imagens: List[Dict[str, Any]] = []
        for img in contexto.imagens_referenciadas[:3]:
            try:
                data = img.path.read_bytes()
                img_b64 = base64.b64encode(data).decode("utf-8")
                imagens.append({
                    "id": img.id,
                    "tipo": img.tipo.value,
                    "formato": img.formato,
                    "dimensoes": img.dimensoes,
                    "base64": f"data:image/{img.formato};base64,{img_b64}",
                    "entidades": img.entidades_relacionadas,
                })
            except Exception as e:
                print(f"   [AVISO] Erro ao carregar imagem {img.id}: {e}")
        return imagens

    def indexar_pdf_visual(
        self, pdf_path: str, extrair_tudo: bool = False
    ) -> Dict[str, Any]:
        """Indexa PDF adicionando elementos visuais ao sistema."""
        print(f"\nIndexando visualmente: {pdf_path}")
        elementos = self.visual.processar_pdf(pdf_path, extrair_tudo)
        self._construir_indice_visual()
        descricoes_geradas: List[Dict[str, Any]] = []
        for elem in elementos:
            for ent in elem.entidades_relacionadas:
                desc = self._gerar_descricao_imagem(elem, ent)
                descricoes_geradas.append({
                    "entidade": ent,
                    "descricao": desc,
                    "imagem_id": elem.id,
                })
        por_tipo: Dict[str, int] = {}
        for e in elementos:
            t = e.tipo.value
            por_tipo[t] = por_tipo.get(t, 0) + 1
        return {
            "elementos_processados": len(elementos),
            "por_tipo": por_tipo,
            "descricoes_geradas": len(descricoes_geradas),
            "entidades_indexadas": len(self.entity_image_index),
        }

    def gerar_encontro_visual(
        self,
        descricao: str,
        referencia_imagem: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Gera encontro inspirado em referencia visual."""
        contexto: Dict[str, Any] = {
            "tema_visual": referencia_imagem,
            "descricao_ambientacao": descricao,
        }
        resultado = self.generator.gerar(
            f"crie encontro inspirado em: {descricao}",
            contexto,
        )
        if (
            referencia_imagem
            and referencia_imagem in self.visual.elementos
        ):
            img = self.visual.elementos[referencia_imagem]
            resultado["sugestao_visual"] = {
                "referencia": img.to_dict(),
                "descricao_tema": self._gerar_descricao_imagem(
                    img, "referencia"
                ),
            }
        return resultado


def demo_multimodal() -> SistemaMultimodal3DT:
    """Demonstracao do sistema multimodal completo."""
    print("=" * 80)
    print("SISTEMA 3D&T MULTIMODAL - NIVEIS 4-7.5 INTEGRADOS")
    print("=" * 80)

    sistema = SistemaMultimodal3DT(campaign_name="Demo Multimodal")
    sistema.iniciar_sessao(1)
    sistema.campanha.adicionar_personagem(
        "Thorin", "pc", "Anao", 2, xp_inicial=500
    )

    print("\n" + "=" * 80)
    print("CONSULTAS DE DEMONSTRACAO")
    print("=" * 80)

    consultas = [
        "mostre-me a imagem de um goblin",
        "descreva o mapa da dungeon",
        "crie encontro medio para 4 jogadores",
    ]
    for query in consultas:
        resposta = sistema.consultar(query, incluir_visuais=True)
        print(f"\nRESULTADO PARA: '{query}'")
        tv = resposta.tipo_consulta_visual
        print(
            f"   Tipo: {tv.value if tv else 'texto puro'}"
        )
        print(f"   Tem conteudo visual: {resposta.tem_conteudo_visual()}")
        if resposta.contexto_visual:
            cv = resposta.contexto_visual
            print(f"   Imagens: {len(cv.imagens_referenciadas)}")
            print(f"   Mapas: {len(cv.mapas_ativos)}")
            print(f"   Fichas OCR: {len(cv.fichas_ocr)}")
        if resposta.imagens_para_exibir:
            print(
                f"   Pronto para exibir: {len(resposta.imagens_para_exibir)} imagem(ns) base64"
            )
        print("   Sugestoes:")
        for s in resposta.sugestoes[:3]:
            print(f"      - {s}")

    print(f"\n{'='*80}")
    sistema.finalizar_sessao("Demo multimodal concluida")

    print("\n[OK] Sistema Multimodal 3D&T completo!")
    print("   Integracoes ativas:")
    print("   - Nivel 4: Raciocinio Inteligente")
    print("   - Nivel 5: Geracao Contextual")
    print("   - Nivel 6: Memoria de Campanha")
    print("   - Nivel 7: Processamento Visual")
    print("   - Nivel 7.5: Integracao Multimodal")
    return sistema


if __name__ == "__main__":
    demo_multimodal()
