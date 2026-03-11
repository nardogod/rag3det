#!/usr/bin/env python3
"""
Gera frontend/src/data/itens_3dt.json a partir de:
- data/processed/itens_magicos/itens_por_categoria.txt (Manual da Magia)
- data/processed/itens_magicos/itens_magicos_canonico.json (stats completos)
- data/processed/itens_magicos/itens_magicos_extraidos_agressivo.json (descrições do PDF)
- Pertences pessoais do Manual (corda, mochila, etc.)

Para extrair descrições do PDF: python scripts/extrair_itens_magicos_agressivo.py
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Mapeamento categoria txt -> tipo frontend
CATEGORIA_PARA_TIPO = {
    "Habilidade de Arma Especial": "Armas",
    "Arma Nomeada": "Armas",
    "Armadura": "Armaduras",
    "Habilidade de Armadura": "Armaduras",
    "Escudo": "Armaduras",
    "Material Especial": "Equipamento",
    "Cajado": "Itens mágicos",
    "Bastão": "Itens mágicos",
    "Anel": "Itens mágicos",
    "Poção": "Poções",
    "Óleo": "Poções",
    "Pomada": "Poções",
    "Ingrediente/Veneno": "Outros",
    "Bônus Genérico": "Outros",
    "Item Diverso": "Itens mágicos",
}

# Pertences pessoais (Manual p. 9)
PERTENCES = [
    ("Corda", "Equipamento", "", "Objeto comum"),
    ("Mochila", "Equipamento", "", "Objeto comum"),
    ("Rádio", "Equipamento", "", "Objeto comum"),
    ("Fósforos", "Equipamento", "", "Objeto comum"),
    ("Tocha", "Equipamento", "", "Objeto comum"),
    ("Lanterna", "Equipamento", "", "Objeto comum"),
    ("Cantil", "Equipamento", "", "Objeto comum"),
    ("Aljava", "Equipamento", "", "Objeto comum"),
]

# Armas básicas (não mágicas)
ARMAS_BASICAS = [
    ("Adaga", "Armas", "", "Arma corpo a corpo"),
    ("Arco", "Armas", "", "Arma à distância"),
    ("Espada", "Armas", "", "Arma corpo a corpo"),
    ("Lança", "Armas", "", "Arma corpo a corpo"),
    ("Maça", "Armas", "", "Arma corpo a corpo"),
]

# Itens obrigatórios do manual 3D&T Alpha (Objetos Mágicos) — garantem coerência
ITENS_OBRIGATORIOS = [
    ("Cura & Magia Menores", "Poções", "", "5 PE", "Restaura 5 PVs e 5 PMs. Item de cura combinado."),
    ("Cura & Magia Maiores", "Poções", "", "15 PE", "Restaura 10 PVs e 10 PMs. Item de cura combinado."),
    ("Cura & Magia Totais", "Poções", "", "30 PE", "Restaura todos os PVs e PMs. Item de cura combinado."),
    ("Brincos de Wynna", "Itens mágicos", "", "5 PE cada", "Cada brinco armazena 1 PM que o usuário pode utilizar quando quiser. Podem ser usados em várias partes do corpo, em qualquer quantidade (qualquer número conta como um único acessório)."),
]


def parse_itens_txt():
    """Parse itens_por_categoria.txt"""
    path = BASE / "data" / "processed" / "itens_magicos" / "itens_por_categoria.txt"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    itens = []
    categoria_atual = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # --- Categoria (N itens) ---
        m = re.match(r"^---\s+(.+?)\s+\(\d+\s+itens\)\s+---$", line)
        if m:
            categoria_atual = m.group(1).strip()
            continue
        # • Nome | Preço: X
        m = re.match(r"^•\s+(.+?)\s+\|\s+Preço:\s*(.*)$", line)
        if m and categoria_atual:
            nome = m.group(1).strip()
            custo = m.group(2).strip() or ""
            if nome and nome != "... e mais 37":
                tipo = CATEGORIA_PARA_TIPO.get(categoria_atual, "Outros")
                itens.append({
                    "nome": nome,
                    "tipo": tipo,
                    "bonus": "",
                    "custo": custo,
                    "efeito": "",
                    "livro": "Manual da Magia",
                })
    return itens


def load_canonico():
    """Carrega itens com stats completos"""
    path = BASE / "data" / "processed" / "itens_magicos" / "itens_magicos_canonico.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {it["nome"]: it for it in data}


def livro_label(livro: str) -> str:
    """Converte nome do PDF em label legível."""
    if not livro:
        return "Manual da Magia"
    l = livro.lower()
    if "manual" in l and "magia" in l and "alpha" not in l:
        return "Manual da Magia"
    if "manual" in l and "magia" in l and "alpha" in l:
        return "Manual da Magia Alpha"
    if "monstros" in l:
        return "Manual dos Monstros"
    if "bestiario" in l or "bestiário" in l:
        return "Bestiário"
    if "aventureiro" in l:
        return "Manual do Aventureiro"
    if "drag" in l:
        return "Manual dos Dragões"
    if "turbinado" in l or "revisado" in l:
        return "Manual Turbinado"
    if "tormenta" in l:
        return "Tormenta"
    if "biblioteca" in l and "elfica" in l:
        return "Manual 3D&T Alpha" if "alpha" in l else "Manual 3D&T"
    if "arcano" in l:
        return "Arcano"
    # Fallback: extrai nome razoável do PDF
    if l.endswith(".pdf"):
        return livro[:-4][:40]
    return livro[:40]

def load_categorizados():
    """Carrega TODOS os itens do categorizados (todas as fontes)."""
    path = BASE / "data" / "processed" / "itens_magicos" / "itens_magicos_categorizados.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


# Fragmentos de descrição que não são nomes de item (sincronizar com popular_canonico_completo.py)
_FRAGMENTOS = {
    "anel tem", "anel aos", "anel parece", "anel saia", "anel estiver", "anel se parece",
    "anel é capaz", "anel nem", "anel são", "anel cujo", "anel e uma", "anel magico toma",
    "anel mágico torna", "anel capaz de", "anel é uma", "anel arcano um mago",
    "anel com três pedras oferecerá", "anel com uma", "anel com uma gema incrustada",
    "anel consome", "anel da revelação da loucura oferece", "anel de anula",
    "anel de força se aplicam", "anel de força sempre é ornamentado",
    "anel de ouro usa energia mágica", "anel dos desejos permite",
    "anel elemental oferece", "anel em seus", "anel estiver no dedo",
    "anel ganha a capacidade de", "anel mágico era visto", "anel mágico é colocado",
    "anel mágicona mesma mão", "anel nunca pode armazenar", "anel não",
    "anel oferece ao seu usuário", "anel parece um belo", "anel pode usar o poder da",
    "anel poderá", "anel prateado tem uma ou mais", "anel sempre leva o nome",
    "anel são itens", "anel são os pri", "anel torna o usuário imune", "anel torna-se cin",
    "anel torna-se mais ágil", "anel é colocado no dedo", "anel é conjurado",
    "anel é considerado", "anel é encontrado o mestre", "anel é um item raro",
    "anel é uma versão", "poção acaba", "poção não veja", "poção tem uma",
    "poção ela é", "poção ele é", "poção adquire", "poção conseguirá", "poção torna",
    "poção teria", "poção permite", "poção perdura", "poção de Explosão deve se",
    "poção de forma errada", "poção vai levar", "poção faz", "poção é usada",
    "pergaminho mágico", "pergaminho a magia", "pergaminho contém", "pergaminho consigo",
    "pergaminho com", "pergaminho mágico é relativa", "pergaminho se",
    "não veja", "sando o machado", "tador conjure", "da Força Infinita",
    "tornável", "remessável", "benefícios", "chado de batalha", "habilidades Arremessável",
    "mas tem a habilidade", "custo em PMs", "ção pela metade", "nenosa",
    "com as habilidades", "tência dos alvos", "contra fogo", "com seus PVs",
    "elixir é muito", "que confere Ataque Múltiplo", "da Força Infinita encontra-se",
    "só vai fazer efeito quando", "deve ser arremessada", "não adianta esfregar",
    "armadura extra a corte", "armadura extra com as mesmas", "armadura extra contra aquele",
    "armadura extra contra ataques", "armadura extra contra dano físico e",
    "armadura extra contra danos causados", "armadura extra contra magias que",
    "armadura extra contra o", "armadura extra contra quaisquer", "armadura extra contra qualquer ataque",
    "armadura extra contra qualquer tipo", "armadura extra contra todos os",
    "armadura extra contra um", "armadura extra e", "armadura extra ou invulnerabilidade",
    "armadura mental está", "armadura natural do poder", "armadura até o",
    "armadura da vítima", "armadura de mzzileyn", "armadura do alvo",
    "armadura do oponente", "armadura do usuário", "armadura do usuário quando",
    "armadura dos alvos", "armadura e resistência e", "armadura funciona",
    "armadura ou força de defesa", "armadura ou em força", "armadura pela metade",
    "armadura que vai de", "armadura será a mais alta", "armadura será dobrada",
    "armadura é multiplicada", "armadura elétrica ótima para se",
    "anel do dragão vermelho torna", "anel com essa famílias", "anel torna seu",
    "anel de anulação de", "poção com o mesmo efeito", "poção criada a partir",
    "poção deve gastar pms", "poção dura por", "poção pode não ser", "poção que adicione",
    "poção recupera", "poção rende", "poção de força tinha como",
    "pergaminho até", "poções são mais facilmente encontradas",
    "olhe para o lado", "allque especial", "ataque erpeclal", "ataque especlal",
    "i xi", "extra a frio e ainda", "extra contra qualquer magia",
    "lança irá atrair", "lança infalível de", "manto da sorte envolve", "manto do",
    "escudo especial é um item", "paraelementais da fumaç",
}

_FRAGMENTOS_EXATOS = {
    "anel de", "anel mágico", "anel arcano um",
    "com seus pvs e pms no máximo", "custo em pms",
    "da força infinita encontra-se perdido em um",
    "poção de explosão deve se", "poção ele", "poção que",
    "que confere ataque múltiplo",
    "pergaminho de cura",
    "poções são mais facilmente encontradas no comércio que",
}

# Nomes que não são itens mágicos (locais, reinos, benefícios de patrono, etc.)
_NAO_ITENS = {
    "caverna do dragão",  # reino/benefício de patrono, não item
}

# Categorias que indicam habilidade de arma/armadura (não item físico)
_CATEGORIAS_HABILIDADE = {"Habilidade de Arma Especial", "Habilidade de Armadura"}

# Categorias de itens físicos (armaduras, armas, anéis, cajados, etc.) — só estas entram
_CATEGORIAS_ITEM_FISICO = {
    "Arma Nomeada", "Armadura", "Escudo", "Cajado", "Bastão", "Anel",
    "Poção", "Pocao", "Óleo", "oleo", "Pomada", "Material Especial",
    "Item Diverso", "Ingrediente/Veneno",
}

# Categorias excluídas (habilidades, bônus genéricos)
_CATEGORIAS_EXCLUIDAS = {
    "Habilidade de Arma Especial", "Habilidade de Armadura", "Bônus Genérico",
}

# Livros que têm seção de Objetos Mágicos/equipamento — itens de outras seções são ignorados
_LIVROS_SECAO_ITENS = {
    "Manual da Magia", "Manual da Magia Alpha", "Manual 3D&T Alpha",
    "Manual Turbinado", "Manual do Aventureiro",
}

# Substring: nomes que contêm estes padrões são fragmentos (sincronizar com popular_canonico)
_FRAGMENTOS_SUBSTRING = {
    "armadura elétrica ótima para", "armadura mental está", "armadura funciona",
    "armadura extra contra o", "armadura extra contra um", "armadura extra contra aquele",
    "armadura extra contra todos os", "armadura extra contra quaisquer",
    "armadura extra contra ataques baseados", "armadura extra contra dano físico e",
    "armadura extra contra danos causados", "armadura extra contra magias que",
    "armadura extra contra qualquer ataque", "armadura extra contra qualquer tipo",
    "armadura extra contra um tipo específico", "armadura extra e resistência",
    "armadura extra e restrição", "armadura extra a corte",
}


def _eh_efeito_beneficio_patrono(efeito: str) -> bool:
    """Detecta descrições de benefício de patrono/reino, não item físico."""
    if not efeito or len(efeito) < 50:
        return False
    ef = efeito.strip().lower()
    if "reino é capaz de fornecer" in ef or "patrono:" in ef or "patrono " in ef[:80]:
        return True
    if "reino de " in ef[:100] and "é capaz" in ef:
        return True
    return False


def _eh_fragmento(nome: str) -> bool:
    """Detecta nomes que são fragmentos de frase, não itens."""
    n = (nome or "").strip().lower()
    if not n or len(n) < 4:
        return True
    if len(n) > 55:
        return True
    if n.endswith("-") or " -" in n:
        return True
    if n in _NAO_ITENS or n in _FRAGMENTOS_EXATOS:
        return True
    if any(f in n for f in _FRAGMENTOS_SUBSTRING):
        return True
    if any(p in n for p in [" só vai ", " quando a ", " quando o ", " não adianta ",
                            " um mago ", " oferece ", " permite ao ", " é capaz de ",
                            " envolve o usuário", " conta como se", " será a mais alta",
                            " será dobrada", " é multiplicada", " vai de ", " até o "]):
        return True
    if re.search(r"(armadura|anel|manto|escudo)\s+(do|da|de)\s+(alvo|oponente|vítima|usuário)", n):
        return True
    if re.search(r"[a-záàâãéêíóôõúç]-\s", n) or re.search(r"\w+-\s*$", n):
        return True
    if re.match(r"^[ivxlcdm]+\s+[ivxlcdm]+$", n):
        return True
    return False


def extract_custo(efeito):
    """Tenta extrair custo do campo efeito (pode ter lixo de OCR)"""
    if not efeito or len(efeito) > 500:  # efeito muito longo = provavelmente lixo
        return ""
    m = re.search(r"Preço:\s*([^.\n]+)", efeito)
    if m:
        return m.group(1).strip()[:80]
    m = re.search(r"T\$\s*[\d.,]+", efeito)
    if m:
        return m.group(0)
    return ""


def normalizar_legibilidade(s: str) -> str:
    """Melhora a legibilidade: espaços, pontuação, hifenização quebrada."""
    if not s or len(s) < 10:
        return s
    s = re.sub(r" +", " ", s)
    s = re.sub(r"(\w)-\s+", r"\1", s)
    s = re.sub(r"([.!?,;:])([A-Za-zÀ-ÿ])", r"\1 \2", s)
    s = re.sub(r" +([.,;:!?])", r"\1", s)
    return s.strip()


def efeito_valido(efeito: str) -> bool:
    """Descarta efeitos com lixo de OCR (descrições de monstros)"""
    if not efeito or len(efeito) < 20:
        return False
    if len(efeito) > 1500:  # muito longo = provavelmente pegou texto de monstro
        return False
    # Palavras que indicam descrição de monstro, não de item
    lixo = ["ankheg", "aparição", "aparição tórrida", "aranea", "múmia", "lich",
            "lobo atroz", "ameba gigante", "carrasco", "abutre atroz", "planetário",
            "ninfa pacífica", "ninfa agressiva", "unicórnio", "urso-coruja"]
    ef_lower = efeito.lower()
    if any(p in ef_lower for p in lixo):
        return False
    return True


def load_extraidos():
    """Carrega itens extraídos do PDF (prioriza Manual da Magia para descrições)"""
    path = BASE / "data" / "processed" / "itens_magicos" / "itens_magicos_extraidos_agressivo.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    # Por nome: escolhe a melhor entrada (prioridade: manual-da-magia SEM alpha)
    by_nome: dict[str, dict] = {}
    for it in data:
        nome = (it.get("nome") or "").strip()
        if not nome or len(nome) < 3:
            continue
        livro = it.get("livro") or ""
        # Prioridade: manual-da-magia (não alpha) > alpha manual > bestiário
        prioridade = 0
        if "manual" in livro.lower() and "magia" in livro.lower():
            prioridade = 2 if "alpha" not in livro.lower() else 1
        efeito = (it.get("efeito") or "").strip()
        if not efeito_valido(efeito):
            efeito = ""
        atual = by_nome.get(nome, {})
        atual_prior = 0
        if atual.get("livro"):
            atual_prior = 2 if "alpha" not in (atual.get("livro") or "").lower() else 1
        # Fallback: texto_bruto se efeito inválido (Manual da Magia)
        if not efeito and prioridade >= 1:
            tb = (it.get("texto_bruto") or "").strip()
            if tb and 50 < len(tb) < 800 and efeito_valido(tb[:600]):
                efeito = tb[:600]
        if prioridade > atual_prior or (prioridade == atual_prior and efeito and not atual.get("efeito")):
            custo = it.get("custo") or extract_custo(it.get("efeito") or it.get("texto_bruto") or "")
            by_nome[nome] = {
                "nome": nome,
                "bonus": it.get("bonus") or "",
                "custo": custo,
                "efeito": (efeito[:1500] if efeito else ""),  # recorte completo
                "livro": livro,
            }
    return by_nome


def main():
    itens_txt = parse_itens_txt()
    canonico = load_canonico()
    categorizados = load_categorizados()
    extraidos_raw = json.loads(
        (BASE / "data" / "processed" / "itens_magicos" / "itens_magicos_extraidos_agressivo.json").read_text(encoding="utf-8")
    ) if (BASE / "data" / "processed" / "itens_magicos" / "itens_magicos_extraidos_agressivo.json").exists() else []

    cat_para_tipo = {
        "Item Diverso": "Itens mágicos", "Bônus Genérico": "Outros",
        "Habilidade de Arma Especial": "Armas", "Habilidade de Armadura": "Armaduras",
        "Anel": "Itens mágicos", "Arma Nomeada": "Armas", "Poção": "Poções", "Pocao": "Poções",
        "Armadura": "Armaduras", "Cajado": "Itens mágicos", "Escudo": "Armaduras",
        "Ingrediente/Veneno": "Outros", "Bastão": "Itens mágicos", "Material Especial": "Equipamento",
        "Pomada": "Poções", "Óleo": "Poções", "oleo": "Poções",
    }
    txt_por_nome = {it["nome"]: it for it in itens_txt}

    # Chave (nome, livro) para evitar duplicatas da mesma fonte
    vistos: set[tuple[str, str]] = set()
    out: list[dict] = []

    def add_entry(nome: str, tipo: str, bonus: str, custo: str, efeito: str, livro: str, natureza: str = "Item"):
        key = (nome.strip(), livro)
        if key in vistos:
            return
        vistos.add(key)
        out.append({
            "nome": nome.strip(),
            "tipo": tipo,
            "bonus": bonus,
            "custo": custo,
            "efeito": efeito,
            "livro": livro,
            "natureza": natureza,
        })

    # 1. Linhas do categorizados — só categorias de itens físicos (exclui habilidades, bônus genérico)
    for it in categorizados:
        nome = (it.get("nome") or "").strip()
        if not nome or len(nome) < 2 or _eh_fragmento(nome):
            continue
        cat = it.get("categoria_label") or ""
        if cat not in _CATEGORIAS_ITEM_FISICO:
            continue
        tipo = cat_para_tipo.get(cat, "Outros")
        natureza = "Habilidade" if cat in _CATEGORIAS_HABILIDADE else "Item"
        efeito_raw = (it.get("efeito") or "").strip()
        efeito = efeito_raw[:1500] if efeito_raw else ""
        custo = it.get("custo") or extract_custo(efeito_raw)
        livro = livro_label(it.get("livro") or "")
        add_entry(nome, tipo, it.get("bonus") or "", custo, efeito, livro, natureza)

    # 2. Linhas do extraídos — só livros com seção de itens (exclui monstros, bestiário, etc.)
    for it in extraidos_raw:
        nome = (it.get("nome") or "").strip()
        if not nome or len(nome) < 2 or _eh_fragmento(nome):
            continue
        livro = livro_label(it.get("livro") or "")
        if livro not in _LIVROS_SECAO_ITENS:
            continue
        if (nome, livro) in vistos:
            continue
        efeito = (it.get("efeito") or "").strip()
        if not efeito_valido(efeito):
            efeito = (it.get("texto_bruto") or "")[:600] if efeito_valido((it.get("texto_bruto") or "")[:600]) else ""
        add_entry(nome, "Itens mágicos", it.get("bonus") or "", it.get("custo") or extract_custo(it.get("efeito") or ""), efeito[:1500], livro)

    # 3. Sobrescreve custo com txt quando disponível
    for it in itens_txt:
        nome = it["nome"]
        for e in out:
            if e["nome"] == nome and it.get("custo"):
                e["custo"] = it["custo"]
                break
        else:
            if nome not in [x["nome"] for x in out]:
                add_entry(nome, it.get("tipo", "Outros"), "", it.get("custo", ""), "", "Manual da Magia")

    # 4. Pertences e armas básicas
    desc_p = "Equipamento comum de aventura. Item de uso geral em explorações, acampamentos e viagens."
    desc_a = "Arma básica de combate. Equipamento padrão sem propriedades mágicas."
    for nm, tp, bn, cu in PERTENCES:
        add_entry(nm, tp, bn, cu, desc_p, "Manual Turbinado")
    for nm, tp, bn, cu in ARMAS_BASICAS:
        add_entry(nm, tp, bn, cu, desc_a, "Manual Turbinado")
    for nm, tp, bn, cu, ef in ITENS_OBRIGATORIOS:
        add_entry(nm, tp, bn, cu, ef, "Manual 3D&T Alpha")

    # 5. Canonico enriquece (atualiza efeito quando melhor) e adiciona itens CURADOS ausentes
    for nome, c in canonico.items():
        if _eh_fragmento(nome):
            continue
        ce = (c.get("efeito") or "").strip()
        ja_existe = any(e["nome"] == nome for e in out)
        if ja_existe:
            if len(ce) >= 30:
                cat_c = c.get("categoria_label") or ""
                nat_c = "Habilidade" if cat_c in _CATEGORIAS_HABILIDADE else "Item"
                for e in out:
                    if e["nome"] == nome and len((e.get("efeito") or "").strip()) < len(ce):
                        e["bonus"] = c.get("bonus") or e.get("bonus", "")
                        e["custo"] = c.get("custo") or e.get("custo", "")
                        e["efeito"] = ce[:1500]
                        e["livro"] = c.get("livro") or e.get("livro", "")
                        e["natureza"] = nat_c
        elif len(ce) >= 20:
            cat_c = c.get("categoria_label") or ""
            if cat_c in _CATEGORIAS_EXCLUIDAS or cat_c not in _CATEGORIAS_ITEM_FISICO:
                continue
            nat_c = "Habilidade" if cat_c in _CATEGORIAS_HABILIDADE else "Item"
            add_entry(nome, c.get("tipo") or "Outros", c.get("bonus") or "", c.get("custo") or "", ce[:1500], c.get("livro") or "Manual 3D&T Alpha", nat_c)

    # 6. Garante descrição legível e natureza (habilidade vs item)
    FALLBACK = "Item citado em fontes. Descrição não disponível nas fontes consultadas."
    for e in out:
        ef = (e.get("efeito") or "").strip()
        e["efeito"] = normalizar_legibilidade(ef) if len(ef) >= 20 else FALLBACK
        if "natureza" not in e:
            c = canonico.get(e["nome"])
            cat = (c.get("categoria_label") or "") if c else ""
            e["natureza"] = "Habilidade" if cat in _CATEGORIAS_HABILIDADE else "Item"

    # 7. Deduplica por nome: mantém uma entrada por item, preferindo livro com seção de itens e descrição
    by_nome: dict[str, dict] = {}
    for e in out:
        nome = e["nome"]
        ef = (e.get("efeito") or "").strip()
        tem_desc = ef and ef != FALLBACK and len(ef) >= 30
        livro_ok = e.get("livro") in _LIVROS_SECAO_ITENS
        if nome not in by_nome:
            by_nome[nome] = e
        else:
            atual = by_nome[nome]
            ef_atual = (atual.get("efeito") or "").strip()
            tem_desc_atual = ef_atual and ef_atual != FALLBACK and len(ef_atual) >= 30
            livro_ok_atual = atual.get("livro") in _LIVROS_SECAO_ITENS
            # Preferir: 1) livro com seção itens; 2) com descrição real; 3) descrição mais longa
            if livro_ok and not livro_ok_atual:
                by_nome[nome] = e
            elif livro_ok == livro_ok_atual:
                if tem_desc and not tem_desc_atual:
                    by_nome[nome] = e
                elif (tem_desc and tem_desc_atual) or (not tem_desc and not tem_desc_atual):
                    if len(ef) > len(ef_atual):
                        by_nome[nome] = e
    out = list(by_nome.values())

    # 8. Quando canônico tem descrição curada, usa como fonte preferencial
    for e in out:
        c = canonico.get(e["nome"])
        if not c:
            continue
        ce = (c.get("efeito") or "").strip()
        if 30 <= len(ce) <= 1500:
            ef = (e.get("efeito") or "").strip()
            if ef == FALLBACK or len(ef) < len(ce) or (len(ef) > 800 and len(ce) < 200):
                e["efeito"] = ce[:1500]
                e["bonus"] = c.get("bonus") or e.get("bonus", "")
                e["custo"] = c.get("custo") or e.get("custo", "")
                e["livro"] = c.get("livro") or e.get("livro", "")
                cat = c.get("categoria_label") or ""
                e["natureza"] = "Habilidade" if cat in _CATEGORIAS_HABILIDADE else "Item"

    # 9. Filtra: só itens físicos de livros com seção de Objetos Mágicos
    out = [
        e for e in out
        if e.get("natureza") != "Habilidade"
        and e.get("livro") in _LIVROS_SECAO_ITENS
        and (canonico.get(e["nome"]) or {}).get("categoria_label") not in _CATEGORIAS_EXCLUIDAS
        and (e.get("nome") or "").strip().lower() not in _NAO_ITENS
        and not _eh_efeito_beneficio_patrono(e.get("efeito") or "")
    ]

    out.sort(key=lambda x: (x["tipo"], x["nome"], x["livro"]))
    out_path = BASE / "frontend" / "src" / "data" / "itens_3dt.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gerado {len(out)} itens em {out_path}")


if __name__ == "__main__":
    main()
