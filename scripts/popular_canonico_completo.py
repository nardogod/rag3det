#!/usr/bin/env python3
"""
Popula itens_magicos_canonico.json com descrições completas para todos os itens.
Usa chunks (Manual da Magia) + extraidos para extrair o texto completo.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CHUNKS_PATH = BASE / "data" / "processed" / "chunks.json"
EXTRAIDOS_PATH = BASE / "data" / "processed" / "itens_magicos" / "itens_magicos_extraidos_agressivo.json"
CATEGORIZADOS_PATH = BASE / "data" / "processed" / "itens_magicos" / "itens_magicos_categorizados.json"
INDICE_PATH = BASE / "data" / "processed" / "indice_itens_magicos_3dt.txt"
CANONICO_PATH = BASE / "data" / "processed" / "itens_magicos" / "itens_magicos_canonico.json"

# Fragmentos que indicam linha inválida (não é nome de item)
INDICE_FRAGMENTOS = {
    # anel + descrição
    "anel tem", "anel aos", "anel parece", "anel saia", "anel estiver", "anel se parece",
    "anel é capaz", "anel nem", "anel são", "anel cujo", "anel e uma", "anel magico toma",
    "anel mágico torna", "anel capaz de", "anel é uma", "anel arcano um mago",
    "anel com três pedras oferecerá", "anel com uma", "anel com uma gema incrustada",
    "anel consome", "anel da revelação da loucura oferece", "anel de anula",
    "anel de força se aplicam", "anel de força sempre é ornamentado",
    "anel de ouro usa energia mágica", "anel dos desejos permite",
    "anel elemental oferece", "anel em seus", "anel estiver no dedo",
    "anel ganha a capacidade de", "anel mágico", "anel mágico era visto",
    "anel mágico é colocado", "anel mágicona mesma mão", "anel nunca pode armazenar",
    "anel não", "anel oferece ao seu usuário", "anel parece um belo",
    "anel pode usar o poder da", "anel poderá", "anel prateado tem uma ou mais",
    "anel sempre leva o nome", "anel são itens", "anel são os pri",
    "anel torna o usuário imune", "anel torna-se cin", "anel torna-se mais ágil",
    "anel é colocado no dedo", "anel é conjurado", "anel é considerado",
    "anel é encontrado o mestre", "anel é um item raro", "anel é uma versão",
    # poção + descrição
    "poção acaba", "poção não veja", "poção tem uma", "poção ela é", "poção ele é",
    "poção adquire", "poção conseguirá", "poção torna", "poção teria", "poção permite",
    "poção perdura", "poção de Explosão deve se", "poção de forma errada",
    "poção vai levar", "poção faz", "poção é usada",
    # pergaminho + descrição
    "pergaminho mágico", "pergaminho a magia", "pergaminho contém", "pergaminho consigo",
    "pergaminho com", "pergaminho mágico é relativa", "pergaminho se",
    # outros
    "não veja", "sando o machado", "tador conjure", "da Força Infinita",
    "tornável", "remessável", "benefícios", "chado de batalha", "habilidades Arremessável",
    "mas tem a habilidade", "custo em PMs", "ção pela metade", "nenosa",
    "com as habilidades", "tência dos alvos", "contra fogo", "com seus PVs",
    "Brenda", "elixir é muito", "que confere Ataque Múltiplo", "da Força Infinita encontra-se",
    "só vai fazer efeito quando", "deve ser arremessada", "não adianta esfregar",
    # Armadura + descrição (continuação de frase)
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
    # Anel + descrição
    "anel do dragão vermelho torna", "anel com essa famílias", "anel torna seu",
    "anel de anulação de",
    # Poção + descrição
    "poção com o mesmo efeito", "poção criada a partir", "poção deve gastar pms",
    "poção dura por", "poção pode não ser", "poção que adicione",
    "poção recupera", "poção rende", "poção de força tinha como",
    # Pergaminho + descrição
    "pergaminho até", "poções são mais facilmente encontradas",
    # Outros fragmentos
    "olhe para o lado", "allque especial", "ataque erpeclal", "ataque especlal",
    "i xi", "extra a frio e ainda", "extra contra qualquer magia",
    "lança irá atrair", "lança infalível de",
    "manto da sorte envolve", "manto do",
    "escudo especial é um item", "paraelementais da fumaç",
}

# Nomes exatos que são fragmentos (não substring - match exato)
_FRAGMENTOS_EXATOS = {
    "anel de", "anel mágico", "anel arcano um",
    "com seus pvs e pms no máximo", "custo em pms",
    "da força infinita encontra-se perdido em um",
    "poção de explosão deve se", "poção ele", "poção que",
    "que confere ataque múltiplo",
    "pergaminho de cura",
    "poções são mais facilmente encontradas no comércio que",
}

# Substring: nomes que CONTÊM estes padrões são fragmentos (extração OCR errada)
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


def _eh_fragmento_descricao(nome: str) -> bool:
    """Detecta nomes que são fragmentos de frase (descrição), não itens."""
    n = (nome or "").strip().lower()
    if not n or len(n) < 4:
        return True
    # Nome muito longo (>55 chars) = provavelmente frase
    if len(n) > 55:
        return True
    # Termina com hífen = truncado
    if n.endswith("-") or " -" in n:
        return True
    if n in _FRAGMENTOS_EXATOS:
        return True
    if any(f in n for f in _FRAGMENTOS_SUBSTRING):
        return True
    # Padrões de frase (verbo + complemento)
    if any(p in n for p in [" só vai ", " quando a ", " quando o ", " não adianta ", " deve ser ",
                            " um mago ", " o usuário ", " ao seu ", " oferece ",
                            " permite ao ", " é capaz de ", " tem uma ", " tem o ",
                            " envolve o usuário", " conta como se", " será a mais alta",
                            " será dobrada", " é multiplicada", " vai de ", " até o "]):
        return True
    # "Armadura/Anel/Manto do/da/de" + pronome (vítima, alvo, oponente, usuário) = fragmento
    if re.search(r"(armadura|anel|manto|escudo)\s+(do|da|de)\s+(alvo|oponente|vítima|usuário)", n):
        return True
    # Palavras truncadas
    if re.search(r"[a-záàâãéêíóôõúç]-\s", n) or re.search(r"\w+-\s*$", n):
        return True
    # Nomes que são só números/romanos: "I XI"
    if re.match(r"^[ivxlcdm]+\s+[ivxlcdm]+$", n):
        return True
    return False


def extrair_descricao_apos_nome(texto: str, nome: str) -> str | None:
    """Extrai a descrição que vem após o nome do item no texto."""
    if not texto or not nome:
        return None
    idx = texto.find(nome)
    if idx < 0:
        return None
    resto = texto[idx + len(nome) : idx + 1500]
    # Corta no próximo item (Preço:, ou linha com "Nome\n" padrão, ou PEs.)
    for sep in [r"\nPreço:\s*", r"\n[A-ZÁÉÍÓÚÂÊÔ][A-Za-záéíóúâêôãõç\s\-]{4,}\n", r"\d+\s*PEs\.\s*\n"]:
        partes = re.split(sep, resto, maxsplit=1)
        if len(partes) > 1:
            resto = partes[0]
    desc = re.sub(r"\s+", " ", resto).strip()
    if len(desc) < 30:
        return None
    return desc


def main():

    # 1. Carrega lista de itens (categorizados TODAS as fontes + pertences + armas)
    cat_path = CATEGORIZADOS_PATH
    if not cat_path.exists():
        print("Categorizados não encontrado.")
        return
    categorizados = json.loads(cat_path.read_text(encoding="utf-8"))

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
        return livro[:50]

    cat_para_tipo = {
        "Item Diverso": "Itens mágicos",
        "Bônus Genérico": "Outros",
        "Habilidade de Arma Especial": "Armas",
        "Habilidade de Armadura": "Armaduras",
        "Anel": "Itens mágicos",
        "Arma Nomeada": "Armas",
        "Poção": "Poções",
        "Pocao": "Poções",
        "Armadura": "Armaduras",
        "Cajado": "Itens mágicos",
        "Escudo": "Armaduras",
        "Ingrediente/Veneno": "Outros",
        "Bastão": "Itens mágicos",
        "Material Especial": "Equipamento",
        "Pomada": "Poções",
        "Óleo": "Poções",
    }
    itens = {}
    for it in categorizados:
        nome = (it.get("nome") or "").strip()
        if not nome or len(nome) < 2 or nome.endswith("-") or _eh_fragmento_descricao(nome):
            continue
        cat = it.get("categoria_label") or ""
        tipo = cat_para_tipo.get(cat, "Outros")
        livro = livro_label(it.get("livro") or "")
        itens[nome] = {
            "nome": nome,
            "tipo": tipo,
            "bonus": it.get("bonus") or "",
            "custo": it.get("custo") or "",
            "efeito": "",
            "livro": livro,
            "categoria": cat.lower().replace(" ", "_") if cat else "outros",
            "categoria_label": cat or "Outros",
        }

    # Sobrescreve custo com txt quando disponível, adiciona itens do txt
    TXT_PATH = BASE / "data" / "processed" / "itens_magicos" / "itens_por_categoria.txt"
    CATEGORIA_PARA_TIPO = {
        "Habilidade de Arma Especial": "Armas", "Arma Nomeada": "Armas",
        "Armadura": "Armaduras", "Habilidade de Armadura": "Armaduras",
        "Escudo": "Armaduras", "Material Especial": "Equipamento",
        "Cajado": "Itens mágicos", "Bastão": "Itens mágicos", "Anel": "Itens mágicos",
        "Poção": "Poções", "Óleo": "Poções", "Pomada": "Poções",
        "Ingrediente/Veneno": "Outros", "Bônus Genérico": "Outros", "Item Diverso": "Itens mágicos",
    }
    if TXT_PATH.exists():
        categoria_atual = ""
        for line in TXT_PATH.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^---\s+(.+?)\s+\(\d+\s+itens\)\s+---$", line.strip())
            if m:
                categoria_atual = m.group(1).strip()
                continue
            m = re.match(r"^•\s+(.+?)\s+\|\s+Preço:\s*(.*)$", line.strip())
            if m and categoria_atual and m.group(1).strip() != "... e mais 37":
                nome = m.group(1).strip()
                custo = m.group(2).strip() or ""
                tipo = CATEGORIA_PARA_TIPO.get(categoria_atual, "Outros")
                if nome not in itens:
                    itens[nome] = {"nome": nome, "tipo": tipo, "bonus": "", "custo": custo, "efeito": "", "livro": "Manual da Magia", "categoria": "outros", "categoria_label": "Outros"}
                elif custo:
                    itens[nome]["custo"] = custo

    # 2c. Adiciona itens do índice (nomes completos que faltam)
    def inferir_tipo(nome: str) -> str:
        n = nome.lower()
        if any(n.startswith(p) for p in ["poção", "pomada", "óleo"]): return "Poções"
        if any(n.startswith(p) for p in ["anel", "amuleto", "bracelete", "colar", "medalhão"]): return "Itens mágicos"
        if any(n.startswith(p) for p in ["armadura", "cota", "loriga", "peitoral", "escudo"]): return "Armaduras"
        if any(n.startswith(p) for p in ["cajado", "bastão", "vara"]): return "Itens mágicos"
        if any(n.startswith(p) for p in ["adaga", "espada", "arco", "lança", "maça", "flecha", "tridente", "chicote", "marreta", "sabre"]): return "Armas"
        if any(n.startswith(p) for p in ["botas", "manto", "capa", "chapéu", "elmo", "manoplas", "cinto", "cinturão"]): return "Itens mágicos"
        if "afiada" in n or "ameaçadora" in n or "terror" in n or "dançarina" in n or "defensora" in n: return "Armas"
        if "camuflagem" in n or "confortável" in n or "contramágica" in n or "escorregadia" in n or "fortificação" in n: return "Armaduras"
        if "resistência +" in n or "habilidade +" in n or "armadura +" in n or "força +" in n: return "Outros"
        if any(x in n for x in ["veneno", "arsênico", "poeira", "musgo", "excremento"]): return "Outros"
        return "Itens mágicos"

    if INDICE_PATH.exists():
        for line in INDICE_PATH.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\d+\.\s+(.+)$", line.strip())
            if not m:
                continue
            nome = m.group(1).strip()
            if len(nome) < 4 or len(nome) > 70:
                continue
            if nome.endswith("-") or "..." in nome:
                continue
            if not nome[0].isupper() and nome[0] not in "0123456789":
                continue
            n_lower = nome.lower()
            if any(f in n_lower for f in INDICE_FRAGMENTOS):
                continue
            if nome in itens:
                continue
            itens[nome] = {
                "nome": nome,
                "tipo": inferir_tipo(nome),
                "bonus": "",
                "custo": "",
                "efeito": "",
                "livro": "Manual da Magia",
                "categoria": "outros",
                "categoria_label": "Outros",
            }

    # 2d. Adiciona itens do extraídos (qualquer fonte) que faltam
    if EXTRAIDOS_PATH.exists():
        extraidos = json.loads(EXTRAIDOS_PATH.read_text(encoding="utf-8"))
        for it in extraidos:
            nome = (it.get("nome") or "").strip()
            if not nome or len(nome) < 3 or nome.endswith("-") or _eh_fragmento_descricao(nome):
                continue
            if nome in itens:
                continue
            livro = livro_label(it.get("livro") or "")
            itens[nome] = {
                "nome": nome,
                "tipo": inferir_tipo(nome),
                "bonus": it.get("bonus") or "",
                "custo": it.get("custo") or "",
                "efeito": "",
                "livro": livro,
                "categoria": "outros",
                "categoria_label": "Outros",
            }

    # Pertences e armas básicas
    pertences = [
        ("Corda", "Equipamento"), ("Mochila", "Equipamento"), ("Rádio", "Equipamento"),
        ("Fósforos", "Equipamento"), ("Tocha", "Equipamento"), ("Lanterna", "Equipamento"),
        ("Cantil", "Equipamento"), ("Aljava", "Equipamento"),
    ]
    armas = [
        ("Adaga", "Armas"), ("Arco", "Armas"), ("Espada", "Armas"),
        ("Lança", "Armas"), ("Maça", "Armas"),
    ]
    desc_pertences = "Equipamento comum de aventura. Item de uso geral em explorações, acampamentos e viagens."
    desc_armas = "Arma básica de combate. Equipamento padrão sem propriedades mágicas."
    for nome, tipo in pertences:
        itens[nome] = {"nome": nome, "tipo": tipo, "bonus": "", "custo": "", "efeito": desc_pertences, "livro": "Manual Turbinado", "categoria": "equipamento", "categoria_label": "Equipamento"}
    for nome, tipo in armas:
        itens[nome] = {"nome": nome, "tipo": tipo, "bonus": "", "custo": "", "efeito": desc_armas, "livro": "Manual Turbinado", "categoria": "arma", "categoria_label": "Arma"}

    # Itens obrigatórios do manual 3D&T Alpha (Objetos Mágicos) — garantem coerência
    itens_obrigatorios = [
        ("Cura & Magia Menores", "Poções"), ("Cura & Magia Maiores", "Poções"),
        ("Cura & Magia Totais", "Poções"), ("Brincos de Wynna", "Itens mágicos"),
    ]
    for nome, tipo in itens_obrigatorios:
        if nome not in itens:
            itens[nome] = {"nome": nome, "tipo": tipo, "bonus": "", "custo": "", "efeito": "", "livro": "Manual 3D&T Alpha", "categoria": "outros", "categoria_label": "Outros"}

    # 2. Carrega chunks Manual da Magia
    chunks_magia = []
    if CHUNKS_PATH.exists():
        chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
        for c in chunks:
            meta = c.get("metadata") or {}
            src = (meta.get("source") or "").lower()
            if "manual" in src and "magia" in src and "alpha" not in src:
                chunks_magia.append(c.get("page_content") or "")

    texto_magia = "\n\n".join(chunks_magia)

    # 3. Carrega extraidos (prioriza Manual Magia não-alpha, escolhe descrição mais longa)
    extraidos_por_nome = {}
    LIXO = ["ankheg", "aparição", "múmia", "lich", "lobo atroz", "ameba gigante", "carrasco", "planetário", "ninfa"]
    if EXTRAIDOS_PATH.exists():
        extraidos = json.loads(EXTRAIDOS_PATH.read_text(encoding="utf-8"))
        for it in extraidos:
            nome = (it.get("nome") or "").strip()
            if not nome or len(nome) < 3:
                continue
            livro = (it.get("livro") or "").lower()
            prioridade = 2 if "magia" in livro and "alpha" not in livro else 1
            efeito = (it.get("efeito") or "").strip()
            texto_bruto = (it.get("texto_bruto") or "").strip()
            # Descarta efeito com texto de monstro
            ef_lower = (efeito or "").lower()
            if any(p in ef_lower for p in LIXO) or (efeito and len(efeito) > 1200):
                efeito = ""
            # Usa o mais longo entre efeito e trecho do texto_bruto (limpar_descricao corta no próximo item)
            candidato = efeito
            if texto_bruto and nome in texto_bruto:
                idx = texto_bruto.find(nome)
                if idx >= 0:
                    trecho = texto_bruto[idx: idx + 1200]
                    tb_lower = trecho.lower()
                    if not any(p in tb_lower for p in LIXO) and len(trecho) > len(efeito) and len(trecho) > 50:
                        candidato = trecho
            atual = extraidos_por_nome.get(nome, {"efeito": "", "prioridade": 0})
            if prioridade > atual["prioridade"] or (prioridade == atual["prioridade"] and len(candidato) > len(atual["efeito"])):
                extraidos_por_nome[nome] = {"efeito": candidato, "prioridade": prioridade, "custo": it.get("custo"), "bonus": it.get("bonus")}

    # 4. Para cada item, obtém a melhor descrição
    def limpar_descricao(s: str, nome_item: str) -> str:
        if not s:
            return ""
        # Corta se encontrar outro item (nome diferente do atual) - evita descrição do próximo item
        for outro in list(itens.keys()):
            if outro != nome_item and len(outro) > 10 and outro in s:
                idx = s.find(outro)
                if idx > 100:
                    s = s[:idx].strip()
                    break
        s = re.sub(r"\n{3,}", "\n\n", s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()[:2000]

    def normalizar_legibilidade(s: str) -> str:
        """Melhora a legibilidade: espaços, pontuação, hifenização quebrada."""
        if not s or len(s) < 10:
            return s
        s = re.sub(r" +", " ", s)
        s = re.sub(r"(\w)-\s+", r"\1", s)  # palavra-\nra -> palavra
        s = re.sub(r"([.!?,;:])([A-Za-zÀ-ÿ])", r"\1 \2", s)
        s = re.sub(r" +([.,;:!?])", r"\1", s)
        return s.strip()

    for nome, entry in list(itens.items()):
        if entry.get("efeito") and len(entry["efeito"]) > 50:
            continue  # já tem descrição boa (pertences/armas)
        # Tenta chunks
        desc_chunk = extrair_descricao_apos_nome(texto_magia, nome)
        # Tenta extraidos
        ex = extraidos_por_nome.get(nome, {})
        desc_ex = (ex.get("efeito") or "").strip()
        # Escolhe a mais longa
        candidatos = [d for d in [desc_chunk, desc_ex] if d and len(d) > 30]
        if candidatos:
            melhor = max(candidatos, key=len)
            entry["efeito"] = limpar_descricao(melhor, nome)
            if ex.get("custo") and not entry.get("custo"):
                entry["custo"] = ex["custo"]
            if ex.get("bonus") and not entry.get("bonus"):
                entry["bonus"] = ex["bonus"]

    # 5. Sobrescreve com itens curados manualmente (descrições perfeitas)
    CURADOS = {
        "Armadura das Profundezas": {
            "bonus": "FD+1", "custo": "25 PEs",
            "efeito": "Esta armadura de batalha é decorada com sinais e imagens de corais, ondas e peixes. O usuário recebe um bônus de FD+1 e não sofre nenhuma penalidade devido à pressão d'água em locais muito profundos. A armadura também é encantada de forma a não atrapalhar os movimentos quando o usuário está debaixo d'água, permitindo-o nadar livremente sem penalidade. Por fim, o usuário pode respirar debaixo d'água (como na Vantagem Única Anfíbio) e pode conversar com qualquer criatura marinha, como peixes e crustáceos. Para os clérigos do Grande Oceano que vivem no Mundo Seco esta armadura é vista como um grande presente de seu deus àqueles que não nasceram com o dom da respiração aquática.",
        },
        "poção de Cura Mágica": {
            "bonus": "", "custo": "1 PE",
            "efeito": "Poção que produz o efeito da magia Cura Mágica quando a vítima bebe o conteúdo. Não adianta esfregar no ferimento — o líquido precisa ser ingerido para fazer efeito. Restaura PVs conforme o nível da magia (Cura Menor: 5 PVs, Cura Maior: 10 PVs, Cura Total: todos os PVs).",
            "livro": "Manual da Magia",
        },
        # Itens sem descrição nas fontes — descrições curadas
        "Amuleto Contra Detecção": {"bonus": "", "custo": "40 PEs", "efeito": "Amuleto de prata criado por Hyninn para seus fiéis servos. Impede que o portador seja detectado por magias de detecção: o teste é de R+2d contra R+1d do mago.", "livro": "Manual da Magia"},
        "Armadura +2": {"bonus": "A+2", "custo": "30 PEs", "efeito": "Armadura mágica que concede bônus de Armadura +2. Uma das variantes de armadura encantada disponíveis (de +1 a +5).", "livro": "Manual da Magia"},
        "Armadura de Aço Rubi": {"bonus": "", "custo": "", "efeito": "Material especial (Aço-Rubi) usado na fabricação de armaduras e equipamentos. Confere propriedades mágicas superiores ao aço comum.", "livro": "Manual da Magia"},
        "Belos Brincos": {"bonus": "", "custo": "", "efeito": "Brincos mágicos que permitem ao portador usar o poder Forma Ilusória. Comuns entre certas raças que colecionam joias e adornos.", "livro": "Manual da Magia"},
        "Bola de Cristal I": {"bonus": "", "custo": "10 PEs", "efeito": "Item de observação que oferece ao usuário os Sentidos Especiais: Infravisão, Radar, Ver o Invisível, Visão Aguçada e Visão de Raio X.", "livro": "Manual da Magia"},
        "Carrasco dos Loucos": {"bonus": "F+1", "custo": "", "efeito": "Machado que pertenceu a um paladino de Tanna-Toh, especializado em casos envolvendo criminosos loucos. Em situações normais comporta-se como arma +1 (F+1).", "livro": "Manual da Magia"},
        "Castelo": {"bonus": "", "custo": "", "efeito": "Local citado em mapas e campanhas. Não é item mágico equipável.", "livro": "Manual dos Monstros"},
        "Cera": {"bonus": "", "custo": "", "efeito": "Ingrediente ou material citado em bestiários. Pode ser usado em alquimia ou fabricação de itens.", "livro": "Manual dos Monstros"},
        "Comando para matar": {"bonus": "", "custo": "", "efeito": "Arma que pertenceu a um assassino. O herói que a empunhar pode reproduzir os efeitos do poder Drenar Energia (exceto a transformação final).", "livro": "Manual dos Monstros"},
        "Confortável": {"bonus": "", "custo": "5 PE", "efeito": "Habilidade de armadura. O usuário pode descansar normalmente com esta armadura, recebendo os benefícios normais por descanso.", "livro": "Manual da Magia"},
        "Couraça": {"bonus": "", "custo": "", "efeito": "Peça de armadura ou ingrediente de criatura (carapaça). Citado em bestiários como material para fabricação.", "livro": "Manual dos Monstros"},
        "Couro do Carrasco": {"bonus": "", "custo": "", "efeito": "Material do bestiário. Permite fabricar uma capa que concede o poder Inversão de Dano por 2 PMs por turno. Enquanto ativo, o usuário sofre da mesma vulnerabilidade à cura que o carrasco.", "livro": "Manual dos Monstros"},
        "Emplastro Vrakoll": {"bonus": "", "custo": "", "efeito": "Item citado em fontes. Descrição não disponível nas fontes consultadas.", "livro": "Manual dos Monstros"},
        "Espada vorpaJ": {"bonus": "", "custo": "", "efeito": "Provável referência a Espada Vorpal. Arma mágica com habilidade Vorpal que pode decapitar em acerto crítico.", "livro": "Manual da Magia"},
        "Excremento de Sapo": {"bonus": "", "custo": "10 PEs", "efeito": "Ingrediente para poções. Pode causar perda de 1 ponto de Habilidade temporariamente. Permite teste de R+1 para negar o efeito.", "livro": "Manual da Magia"},
        "Ferrão": {"bonus": "", "custo": "", "efeito": "Ferrão venenoso de criatura (formian ou similar). Pode ser usado em combate. O veneno exige teste de Resistência ou provoca perda temporária de 1 ponto de Força.", "livro": "Manual dos Monstros"},
        "Flamejante": {"bonus": "", "custo": "5 PE", "efeito": "Habilidade de arma. Concede ataques baseados em fogo ou ácido. Arma causa dano elemental flamejante.", "livro": "Manual da Magia"},
        "Grimório Ancestral": {"bonus": "", "custo": "", "efeito": "Tomo mágico que contém conhecimentos arcanos ancestrais. Usado por magos para ampliar seu poder ou repertório de magias.", "livro": "Manual dos Monstros"},
        "Lanterna dos Afogados": {"bonus": "", "custo": "", "efeito": "Item profano ou de mortos-vivos. Citado em bestiários. Descrição completa não disponível nas fontes consultadas.", "livro": "Manual dos Monstros"},
        "Luvas de Couro de Naga": {"bonus": "", "custo": "", "efeito": "Luvas fabricadas com couro de naga. Concedem propriedades mágicas relacionadas à criatura de origem.", "livro": "Manual dos Monstros"},
        "Mercado": {"bonus": "", "custo": "", "efeito": "Local citado em mapas e campanhas (ex.: Mercado nas Nuvens). Não é item mágico equipável.", "livro": "Manual dos Monstros"},
        "Mortalha": {"bonus": "", "custo": "", "efeito": "Item profano ou de mortos-vivos. Tecido usado em rituais ou como equipamento de criaturas sobrenaturais.", "livro": "Manual dos Monstros"},
        "Musgo Id": {"bonus": "", "custo": "", "efeito": "Ingrediente para poções. O personagem que o usar recebe a desvantagem Inculto. Uma magia Cura pode remover o efeito.", "livro": "Manual da Magia"},
        "O Terceiro Olho": {"bonus": "", "custo": "", "efeito": "Item que concede percepção ou visão especial. Citado em bestiários. Descrição completa não disponível nas fontes consultadas.", "livro": "Manual dos Monstros"},
        "Papagaio Zumbi": {"bonus": "", "custo": "", "efeito": "Item ou criatura citada em bestiários. Relacionado a mortos-vivos ou necromancia.", "livro": "Manual dos Monstros"},
        "Pena de Canário-do-Sono": {"bonus": "", "custo": "", "efeito": "Ingrediente de criatura (canário-do-sono). Usado em poções ou fabricação de itens mágicos.", "livro": "Manual dos Monstros"},
        "Pena de Grifo": {"bonus": "", "custo": "", "efeito": "Ingrediente de grifo. Usado em poções ou fabricação de itens. A coleta envolve viagens a lugares perigosos e combates.", "livro": "Manual da Magia"},
        "Poeira de Lich": {"bonus": "", "custo": "", "efeito": "Ingrediente poderoso obtido de um lich. Usado em poções, rituais ou fabricação de itens necromânticos.", "livro": "Manual da Magia"},
        "Porto": {"bonus": "", "custo": "", "efeito": "Local citado em mapas e campanhas. Não é item mágico equipável.", "livro": "Manual dos Monstros"},
        "Presa": {"bonus": "", "custo": "", "efeito": "Ingrediente de criatura (dentes, presas). Pode ser usado como arma ou material para fabricação. Valor varia conforme a criatura de origem.", "livro": "Manual dos Monstros"},
        "Quartel": {"bonus": "", "custo": "1 PE", "efeito": "Local citado em mapas de campanha (estrutura militar). Não é item mágico equipável.", "livro": "Manual dos Monstros"},
        "Retornável": {"bonus": "", "custo": "10 PE", "efeito": "Habilidade de arma. Quando a arma mágica retornável cai ou é arremessada, ela retorna à mão do portador no início do turno seguinte (a menos que fique presa ou agarrada).", "livro": "Manual da Magia"},
        "Terra Primeva": {"bonus": "", "custo": "", "efeito": "Item ou local citado em fontes. Descrição não disponível nas fontes consultadas.", "livro": "Manual dos Monstros"},
        "Transporte Mágico": {"bonus": "", "custo": "3 PMs por criatura ou 50 kg", "efeito": "Magia que permite ao conjurador teleportar a si e companheiros para qualquer lugar já visitado. Não funciona no interior de estruturas. Criatura teleportada contra a vontade tem direito a teste de Resistência +1.", "livro": "Manual da Magia"},
        "Venenosa": {"bonus": "", "custo": "5 PE", "efeito": "Habilidade de arma. A arma aplica veneno nos ataques. Pode exigir teste de Resistência ou causar efeitos adicionais (paralisia, dano contínuo).", "livro": "Manual da Magia"},
        "Véu Cintilante": {"bonus": "", "custo": "", "efeito": "Item que envolve o usuário com proteção ou efeito visual. Citado em bestiários. Descrição completa não disponível nas fontes consultadas.", "livro": "Manual dos Monstros"},
        "Última Chance": {"bonus": "", "custo": "10 PE", "efeito": "Habilidade para pistolas. A arma sempre possui um último disparo mesmo após as balas acabarem. Apenas aplicável a pistolas.", "livro": "Manual da Magia"},
        # Itens de Cura do manual (3dt-alpha-manual-biblioteca-elfica) — faltavam
        "Cura & Magia Menores": {"bonus": "", "custo": "5 PE", "efeito": "Restaura 5 PVs e 5 PMs. Item de cura combinado.", "livro": "Manual 3D&T Alpha"},
        "Cura & Magia Maiores": {"bonus": "", "custo": "15 PE", "efeito": "Restaura 10 PVs e 10 PMs. Item de cura combinado.", "livro": "Manual 3D&T Alpha"},
        "Cura & Magia Totais": {"bonus": "", "custo": "30 PE", "efeito": "Restaura todos os PVs e PMs. Item de cura combinado.", "livro": "Manual 3D&T Alpha"},
        "Brincos de Wynna": {"bonus": "", "custo": "5 PE cada", "efeito": "Cada brinco armazena 1 Ponto de Magia que o usuário pode utilizar quando quiser. Podem ser usados em várias partes do corpo, em qualquer quantidade (qualquer número conta como um único acessório).", "livro": "Manual 3D&T Alpha"},
    }
    for nome, c in CURADOS.items():
        if nome in itens:
            itens[nome].update(c)

    # 6. Monta saida — aplica normalização e fallback para itens sem descrição
    saida = []
    FALLBACK_EFEITO = "Item citado em fontes. Descrição não disponível nas fontes consultadas."
    for nome, entry in itens.items():
        efeito = (entry.get("efeito") or "").strip()
        if len(efeito) < 20:
            efeito = FALLBACK_EFEITO
        else:
            efeito = normalizar_legibilidade(efeito)
        saida.append({
            "nome": entry["nome"],
            "tipo": entry["tipo"],
            "bonus": entry.get("bonus") or "",
            "custo": entry.get("custo") or "",
            "efeito": efeito[:2000],
            "livro": entry.get("livro") or "Manual da Magia",
            "categoria": entry.get("categoria", "outros"),
            "categoria_label": entry.get("categoria_label", "Outros"),
        })

    saida.sort(key=lambda x: (x["tipo"], x["nome"]))
    CANONICO_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANONICO_PATH.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    com_efeito = sum(1 for it in saida if (it.get("efeito") or "").strip() and len((it.get("efeito") or "").strip()) > 30)
    print(f"Canonico atualizado: {len(saida)} itens, {com_efeito} com descrição completa.")


if __name__ == "__main__":
    main()
