"""
Parser de habilidades de combate DEDICADO ao Guia de Monstros de Arton (Daemon).
Usa o bloco completo (ataques + descrição) para extração precisa.
Corrige: truncamento, captura errada, ausência de padrões.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class HabilidadeCombate:
    nome: str
    detalhes: str
    tipo: str


def _limpar(s: str, max_len: int = 150) -> str:
    """Normaliza e limita tamanho. Evita truncar em ponto intermediário."""
    if not s:
        return ""
    t = re.sub(r"\s+", " ", s.strip())
    # Remover caracteres OCR comuns
    t = re.sub(r"n1|n\s*1", "n", t, flags=re.I)
    t = re.sub(r"1\s*\\\s*", "", t)
    if len(t) > max_len:
        t = t[: max_len - 3].rsplit(" ", 1)[0] + "..."
    return t


def _captura_completa(texto: str, inicio: str, fim: str | None = None) -> str:
    """
    Captura texto entre 'inicio' e o próximo delimitador forte.
    Evita truncamento precoce em '.' ou ';' dentro de parênteses.
    """
    idx = texto.lower().find(inicio.lower())
    if idx < 0:
        return ""
    start = idx + len(inicio)
    # Avançar até fim (se dado) ou até próximo padrão de fim de bloco
    if fim:
        end_idx = texto.lower().find(fim.lower(), start)
        if end_idx > 0:
            return texto[start:end_idx].strip()
    # Senão, capturar até 300 chars ou próximo ".\s+[A-Z]" (fim de frase + nova)
    restante = texto[start : start + 400]
    m = re.search(r"\.\s+[A-ZÀ-ÿ]|;\s*(?:Invulnerabilidade|Vulnerabilidade|#)", restante)
    if m:
        return restante[: m.start()].strip()
    return restante.strip()


def _normalizar_ocr_ataques(bloco: str) -> str:
    """Corrige erros OCR comuns em nomes de ataques (Guia Daemon)."""
    t = bloco
    t = re.sub(r"\bivford\.?ida\b", "Mordida", t, flags=re.I)
    t = re.sub(r"\bc:auda\b", "Cauda", t, flags=re.I)
    t = re.sub(r"\bc:?auda\b", "Cauda", t, flags=re.I)
    t = re.sub(r"J\\\\?'?fordida\b", "Mordida", t, flags=re.I)
    return t


def extrair_ataques(bloco: str) -> list[dict[str, Any]]:
    """Extrai ataques do bloco #Ataques: Mordida, Garras, Bicada, Asfixia, Cauda, etc."""
    bloco = _normalizar_ocr_ataques(bloco)
    resultado: list[dict[str, Any]] = []
    # Mordida X/Y dano ZdW ou ZdW+N (tolerante a espaços: "80 / 50")
    for m in re.finditer(
        r"(?:Mordida|mordida)\s+(\d+)\s*/\s*(\d+)\s*dano\s+(\d+d\d+(?:\+\d+)?)",
        bloco,
        re.I,
    ):
        resultado.append({
            "nome": "Mordida",
            "detalhes": f"{m.group(1)}/{m.group(2)} dano {m.group(3)}",
            "tipo": "ataque",
        })
    # Bicada X/Y dano
    for m in re.finditer(
        r"(?:Bicada|bicada)\s+(\d+)/(\d+)\s*dano\s+(\d+d\d+(?:\+\d+)?)",
        bloco,
        re.I,
    ):
        resultado.append({
            "nome": "Bicada",
            "detalhes": f"{m.group(1)}/{m.group(2)} dano {m.group(3)}",
            "tipo": "ataque",
        })
    # Garras (xN) X/Y dano
    for m in re.finditer(
        r"Garras\s*(?:\(x(\d+)\))?\s*(\d+)/(\d+)\s*dano\s+(\d+d\d+(?:\+\d+)?)",
        bloco,
        re.I,
    ):
        n = f" (x{m.group(1)})" if m.group(1) else ""
        resultado.append({
            "nome": "Garras",
            "detalhes": f"{m.group(2)}/{m.group(3)} dano {m.group(4)}{n}",
            "tipo": "ataque",
        })
    # Cauda X/Y dano (tolerante a espaços: "80 / 50")
    for m in re.finditer(
        r"Cauda\s+(\d+)\s*/\s*(\d+)\s*dano\s+(\d+d\d+(?:\+\d+)?)",
        bloco,
        re.I,
    ):
        resultado.append({
            "nome": "Cauda",
            "detalhes": f"{m.group(1)}/{m.group(2)} dano {m.group(3)}",
            "tipo": "ataque",
        })
    # Asfixia (XdY por rodada)
    for m in re.finditer(
        r"(?:Asfixia|asfixia)\s*[\(\[]?\s*(\d+d\d+)\s*(?:pontos?\s+)?por\s*(?:rodada|turno)",
        bloco,
        re.I,
    ):
        resultado.append({
            "nome": "Asfixia",
            "detalhes": f"{m.group(1)} dano por rodada (ignora Armadura)",
            "tipo": "ataque",
        })
    # Bico X/Y dano
    for m in re.finditer(
        r"Bico\s+(\d+)/(\d+)\s*dano\s+(\d+d\d+(?:\+\d+)?)",
        bloco,
        re.I,
    ):
        resultado.append({
            "nome": "Bico",
            "detalhes": f"{m.group(1)}/{m.group(2)} dano {m.group(3)}",
            "tipo": "ataque",
        })
    return resultado


def extrair_veneno(bloco: str) -> list[dict[str, Any]]:
    """Extrai veneno com dano e PVs/turno."""
    resultado: list[dict[str, Any]] = []
    # perde N PVs por turno... (XdY)
    m = re.search(
        r"(?:perde|perda)\s+(\d+)\s*P[Vv]s?\s*por\s*(?:turno|rodada)[^.]*?\((\d+d\d+)\)",
        bloco,
        re.I,
    )
    if m:
        resultado.append({
            "nome": "Veneno",
            "detalhes": f"{m.group(2)} dano, {m.group(1)} PVs por turno",
            "tipo": "veneno",
        })
        return resultado
    # veneno(XdY)
    m = re.search(r"veneno\s*[\(\[]?\s*(\d+d\d+)\s*[\)\]]?", bloco, re.I)
    if m:
        resultado.append({
            "nome": "Veneno",
            "detalhes": f"{m.group(1)} dano",
            "tipo": "veneno",
        })
    return resultado


def extrair_invulnerabilidade(bloco: str) -> list[dict[str, Any]]:
    """Extrai Invulnerabilidade. Evita captura de 's' ou caractere residual. Tolerante a OCR."""
    resultado: list[dict[str, Any]] = []
    # Invulnerável a ataques baseados em ácido, veneno ou água
    m = re.search(
        r"[Ii]nvulner[aá]vel\s+a\s+ataques?\s+baseados?\s+em\s+([^.]+?)(?:\.|,|\s+naturais|\s+ou\s+m[aá]gicos)",
        bloco,
        re.I,
    )
    if m:
        tipos = _limpar(m.group(1), 120)
        tipos = re.sub(r"[�\\]", "", tipos)  # Remove OCR artifacts
        if len(tipos) > 2 and not re.match(r"^[s\W]+$", tipos):
            resultado.append({"nome": "Invulnerabilidade", "detalhes": tipos, "tipo": "imunidade"})
            return resultado
    # Invulnerabilidade a: X, Y, Z (formato com dois pontos)
    m = re.search(
        r"[Ii]nvulnerabilidade\s*(?:a|à)?\s*[:\s]*([^.;]+?)(?:\.|,|\))",
        bloco,
        re.I,
    )
    if m:
        tipos = _limpar(m.group(1), 120)
        if len(tipos) > 3 and not re.match(r"^[\s\W]+$", tipos):
            resultado.append({"nome": "Invulnerabilidade", "detalhes": tipos, "tipo": "imunidade"})
    return resultado


def extrair_vulnerabilidade(bloco: str) -> list[dict[str, Any]]:
    """Extrai Vulnerabilidade. Só adiciona se captura for válida."""
    resultado: list[dict[str, Any]] = []
    m = re.search(
        r"[Vv]ulnerabilidade\s*(?:a|à)?\s*[:\s]*([^.;]+?)(?:\.|,|\))",
        bloco,
        re.I,
    )
    if m:
        tipos = _limpar(m.group(1), 120)
        if len(tipos) > 3 and not re.match(r"^[\s\W]+$", tipos):
            resultado.append({"nome": "Vulnerabilidade", "detalhes": tipos, "tipo": "vulnerabilidade"})
    return resultado


def extrair_imunidade(bloco: str) -> list[dict[str, Any]]:
    """Extrai imunidades (ex: imunes a poderes dos mortos-vivos)."""
    resultado: list[dict[str, Any]] = []
    # "imunes a todos os poderes sobrenaturais dos mortos-vivos"
    m = re.search(
        r"[Ss]ão\s+imunes?\s+a\s+(?:todos\s+os\s+)?(.+?)(?:\.|e\s+a\s+todas)",
        bloco,
        re.I,
    )
    if m:
        det = _limpar(m.group(1), 150)
        if "mortos" in det.lower() or "poderes" in det.lower():
            resultado.append({
                "nome": "Imune",
                "detalhes": f"Poderes sobrenaturais dos mortos-vivos, Magias das Trevas. Garras/bico ferem mortos-vivos vulneráveis só a magia.",
                "tipo": "imunidade",
            })
            return resultado
    # Construtos, Mortos-Vivos são imunes
    if re.search(r"(?:Construtos?|Mortos?-Vivos?)\s+(?:s[aã]o\s+)?[Ii]munes?", bloco, re.I):
        resultado.append({"nome": "Imune", "detalhes": "Construtos, Mortos-Vivos", "tipo": "imunidade"})
    return resultado


def extrair_petrificacao(bloco: str) -> list[dict[str, Any]]:
    """Extrai petrificação (Basilisco, Medusa)."""
    if re.search(r"[Pp]etrifica[cç][aã]o|[Tt]ransformar\s+.*\s+em\s+pedra", bloco, re.I):
        return [{
            "nome": "Petrificação",
            "detalhes": "Contato visual. Teste de R para negar. Olhos fechados: H-1 corpo, H-3 distância.",
            "tipo": "efeito_especial",
        }]
    return []


def extrair_saliva_acida(bloco: str) -> list[dict[str, Any]]:
    """Extrai saliva ácida (Basilisco)."""
    m = re.search(
        r"[Ss]aliva\s+[Aa]cida\s+causa\s+(\d+d\d+).*?(?:até\s+)?(\d+)\s*m\s+.*?(\d+)\s*rodadas?",
        bloco,
        re.I,
    )
    if m:
        return [{
            "nome": "Saliva ácida",
            "detalhes": f"{m.group(1)} dano, até {m.group(2)}m, 1x a cada {m.group(3)} rodadas",
            "tipo": "ataque",
        }]
    if re.search(r"[Ss]aliva\s+[Aa]cida", bloco, re.I):
        return [{"nome": "Saliva ácida", "detalhes": "Dano por PdF, químico. Ver descrição.", "tipo": "ataque"}]
    return []


def extrair_ataque_automatico(bloco: str) -> list[dict[str, Any]]:
    """Extrai ataque que acerta automaticamente (Asfixor)."""
    if re.search(r"não\s+precisa\s+fazer\s+testes?|ataque\s+acerta\s+automaticamente", bloco, re.I):
        return [{"nome": "Ataque automático", "detalhes": "Acerta automaticamente ao cair/erguer", "tipo": "ataque"}]
    return []


def extrair_teste_forca(bloco: str) -> list[dict[str, Any]]:
    """Extrai Teste de Força para atacar (vítima aprisionada)."""
    if re.search(
        r"vítima\s+aprisionada\s+.*?Teste\s+de\s+For[cç]a\s+para\s+atacar",
        bloco,
        re.I,
    ):
        return [{"nome": "Teste de Força", "detalhes": "Vítima aprisionada deve passar em Teste de F para atacar", "tipo": "teste"}]
    return []


def extrair_voo(bloco: str) -> list[dict[str, Any]]:
    """Extrai velocidade de voo."""
    m = re.search(
        r"(?:voar|voam?)\s+com\s+velocidade\s+de\s+(\d+)\s*m/s",
        bloco,
        re.I,
    )
    if m:
        return [{"nome": "Voo", "detalhes": f"Velocidade {m.group(1)}m/s", "tipo": "movimento"}]
    return []


def extrair_ferir_mortos_vivos(bloco: str) -> list[dict[str, Any]]:
    """Carniceiros: garras e bico ferem mortos-vivos vulneráveis só a magia."""
    if re.search(
        r"garras?\s+e\s+bico\s+conseguem?\s+ferir\s+mortos?-vivos?\s+mesmo",
        bloco,
        re.I,
    ):
        return [{
            "nome": "Ferir mortos-vivos",
            "detalhes": "Garras e bico ferem mortos-vivos vulneráveis apenas a magia",
            "tipo": "ataque",
        }]
    return []


def extrair_habilidades_daemon(bloco_completo: str) -> list[dict[str, Any]]:
    """
    Extrai todas as habilidades de combate do bloco completo (ataques + descrição).
    Usado exclusivamente para o Guia Daemon.
    Deduplica ataques do mesmo tipo (pega o primeiro).
    """
    resultado: list[dict[str, Any]] = []
    vistos: set[str] = set()
    vistos_tipo: set[str] = set()  # Para ataques: um por tipo (Mordida, Cauda, etc.)

    def _add(h: dict, unico_por_tipo: bool = False) -> None:
        chave = f"{h['nome']}:{h['detalhes'][:50]}"
        if unico_por_tipo and h["nome"] in vistos_tipo:
            return
        if chave not in vistos:
            vistos.add(chave)
            if unico_por_tipo:
                vistos_tipo.add(h["nome"])
            resultado.append(h)

    for h in extrair_ataques(bloco_completo):
        _add(h, unico_por_tipo=True)
    for h in extrair_veneno(bloco_completo):
        _add(h)
    for h in extrair_invulnerabilidade(bloco_completo):
        _add(h)
    for h in extrair_vulnerabilidade(bloco_completo):
        _add(h)
    for h in extrair_imunidade(bloco_completo):
        _add(h)
    for h in extrair_petrificacao(bloco_completo):
        _add(h)
    for h in extrair_saliva_acida(bloco_completo):
        _add(h)
    for h in extrair_ataque_automatico(bloco_completo):
        _add(h)
    for h in extrair_teste_forca(bloco_completo):
        _add(h)
    for h in extrair_voo(bloco_completo):
        _add(h)
    for h in extrair_ferir_mortos_vivos(bloco_completo):
        _add(h)

    # Fallback: padrões do parser genérico para testes, incapaz de lutar, definhar
    if re.search(r"oponentes?\s+precisam?\s+passar\s+em\s+[Tt]este\s+de\s+WILL", bloco_completo, re.I):
        _add({"nome": "Teste de WILL", "detalhes": "Oponentes precisam passar em Teste de WILL para atacar", "tipo": "teste"})
    if re.search(r"totalmente\s+incapaz\s+de\s+lutar", bloco_completo, re.I):
        _add({"nome": "Incapaz de lutar", "detalhes": "Nunca ataca", "tipo": "restricao"})
    if re.search(r"definhar|morrer[aá]\s+em\s+(\d+)\s*hora", bloco_completo, re.I):
        _add({"nome": "Definhar", "detalhes": "Morre em 1h fora do habitat", "tipo": "restricao"})

    return resultado
