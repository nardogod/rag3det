"""
Corrige erros OCR comuns em textos extraídos de PDFs/livros digitalizados.
Aplica substituições que tornam o texto legível em português.
"""

from __future__ import annotations

import re


def normalizar_ocr(texto: str) -> str:
    """
    Corrige erros OCR típicos (1→i/m, n1→n/m, con1→com, en1→em, etc.).
    Ex.: "en1 en1boscadas" → "em emboscadas", "n1ais fo1tes" → "mais fortes"
    """
    if not texto or not isinstance(texto, str):
        return texto
    t = texto

    # Remove sequências de lixo (semicolons, artefatos de OCR)
    t = re.sub(r";{3,}[;:·a-zA-Z\s_]*", " ", t)
    t = re.sub(r":[;·]+[a-zA-Z\s]*", " ", t)

    # Sequências específicas (ordem importa: mais específicas primeiro)
    t = re.sub(r"\bcon1\b", "com", t, flags=re.I)
    t = re.sub(r"con1([a-záéíóúâêôãõ])", r"com\1", t, flags=re.I)
    t = re.sub(r"\ben1\b", "em", t, flags=re.I)
    t = re.sub(r"en1([a-záéíóúâêôãõ])", r"em\1", t, flags=re.I)
    t = re.sub(r"\bun1\b", "um", t, flags=re.I)
    t = re.sub(r"un1([a-záéíóúâêôãõ])", r"um\1", t, flags=re.I)
    t = re.sub(r"\btên1\b", "têm", t, flags=re.I)
    t = re.sub(r"\btcn1\b", "tem", t, flags=re.I)
    t = re.sub(r"con1eçar", "começar", t, flags=re.I)
    t = re.sub(r"Radar-\s*1nas", "Radar. Mas", t, flags=re.I)
    t = re.sub(r"1nas\b", "Mas", t, flags=re.I)
    t = re.sub(r"inaiores", "maiores", t, flags=re.I)
    t = re.sub(r"n1ais\b", "mais", t, flags=re.I)
    t = re.sub(r"fo1tes\b", "fortes", t, flags=re.I)
    t = re.sub(r"n1estres\b", "mestres", t, flags=re.I)
    t = re.sub(r"fican1\b", "ficam", t, flags=re.I)
    t = re.sub(r"can1uflagen1", "camuflagem", t, flags=re.I)
    t = re.sub(r"camuflagern\b", "camuflagem", t, flags=re.I)
    t = re.sub(r"c:anuflage1n", "camuflagem", t, flags=re.I)
    t = re.sub(r"folhagen1\b", "folhagem", t, flags=re.I)
    t = re.sub(r"alén1\b", "além", t, flags=re.I)
    t = re.sub(r"notmal\b", "normal", t, flags=re.I)
    t = re.sub(r"percebída", "percebida", t, flags=re.I)
    t = re.sub(r"1\\rn1adura", "Armadura", t, flags=re.I)
    t = re.sub(r"1\s*\\\s*r\s*n1adura", "Armadura", t, flags=re.I)  # 1\rn1adura variantes
    t = re.sub(r"\\\s*ler\s+o\s+Invisível", "ou Ler o Invisível", t, flags=re.I)
    t = re.sub(r"\\\s*1er\s+o\s+Invisível", "ou Ler o Invisível", t, flags=re.I)
    t = re.sub(r"\b1er\b", "ler", t, flags=re.I)
    t = re.sub(r"\bl\s+ima\s+", "Uma ", t, flags=re.I)  # l ima vítima → Uma vítima
    t = re.sub(r"c:an1uflage1n", "camuflagem", t, flags=re.I)
    t = re.sub(r"folha-\s*gem\b", "folhagem", t, flags=re.I)  # hifenização
    t = re.sub(r"prefe-\s*rindo", "preferindo", t, flags=re.I)
    t = re.sub(r"[~:]+fordida\b", "Mordida", t, flags=re.I)  # ~:fordida → Mordida
    t = re.sub(r"P\.'?\s*s\b", "PVs", t, flags=re.I)  # P.' s → PVs
    t = re.sub(r"P\\\.'?\s*s\b", "PVs", t, flags=re.I)  # P\.' s (escaped) → PVs
    t = re.sub(r"Teste\s+de\s+H\s*\.+\s*esistência", "Teste de Resistência", t, flags=re.I)
    t = re.sub(r"H\s*\.+\s*esistência", "Resistência", t, flags=re.I)
    t = re.sub(r"J[\s\\]+aques", "Ataques", t, flags=re.I)  # J aques → Ataques
    t = re.sub(r"J[\s\\]+taques", "Ataques", t, flags=re.I)  # J\taques, J\\taques → Ataques
    t = re.sub(r"t[\s\\]+ndre\.?v", "Andrew", t, flags=re.I)  # t ndre.v → Andrew
    t = re.sub(r"t[\s\\]+dre\.?v", "Andrew", t, flags=re.I)  # t\ndre.v → Andrew (n faltando)
    t = re.sub(r"t\\ndre\\.v", "Andrew", t, flags=re.I)  # t\ndre\.v (literal) → Andrew
    t = re.sub(r"c:c\)N?", "CON", t, flags=re.I)  # c:c)N ou c:c) → CON
    t = re.sub(r"CONN\b", "CON", t, flags=re.I)  # CONN → CON (corrige duplicação)
    t = re.sub(r"C:1'\\?R", "CAR", t, flags=re.I)  # C:1'\R → CAR
    t = re.sub(r"\\X!IJL", "WILL", t, flags=re.I)  # \X!IJL → WILL (backslash literal)
    t = re.sub(r"X!IJL", "WILL", t, flags=re.I)  # X!IJL → WILL (sem backslash)
    t = re.sub(r"i\s*\\?\s*\(\s*;\s*I", "CON", t, flags=re.I)  # i\(;I → CON
    t = re.sub(r"i\s*\\\s*\(\s*;\s*\]", "CON", t, flags=re.I)  # i \ ( ; ] → CON
    t = re.sub(r"\bet1\s+sei\b", "que sei", t, flags=re.I)
    t = re.sub(r"aqtti\b", "aqui", t, flags=re.I)
    t = re.sub(r"assi111\b", "assim", t, flags=re.I)
    t = re.sub(r"\bolbe\b", "olhe", t, flags=re.I)
    t = re.sub(r"ntesv10\b", "nentes", t, flags=re.I)
    t = re.sub(r"Nlas\b", "Mas", t, flags=re.I)
    t = re.sub(r"\bten1\b", "têm", t, flags=re.I)
    t = re.sub(r"plumagen1\b", "plumagem", t, flags=re.I)
    t = re.sub(r"totalrnente\b", "totalmente", t, flags=re.I)
    t = re.sub(r"ne-\s*é,tra\b", "negra", t, flags=re.I)
    t = re.sub(r"n1uito\b", "muito", t, flags=re.I)
    t = re.sub(r"con10\b", "como", t, flags=re.I)
    t = re.sub(r"co1npetições", "competições", t, flags=re.I)
    t = re.sub(r"Porén1\b", "Porém", t, flags=re.I)
    t = re.sub(r"tornan1-se", "tornam-se", t, flags=re.I)
    t = re.sub(r"companheixas\b", "companheiras", t, flags=re.I)
    t = re.sub(r"J\\?\s*sa-Negra", "Asa-Negra", t, flags=re.I)
    t = re.sub(r"\bxton\b", "Arton", t, flags=re.I)
    t = re.sub(r"J\\raques", "Ataques", t, flags=re.I)
    t = re.sub(r"i\\.sfixia", "Asfixia", t, flags=re.I)
    t = re.sub(r"fóle\.?:?go\b", "fôlego", t, flags=re.I)
    t = re.sub(r"I<\.?\s*atabrok", "Katabrok", t, flags=re.I)
    # Carniceiros, Carrasco de Lena e similares
    t = re.sub(r"\(arniceiros", "Carniceiros", t, flags=re.I)
    t = re.sub(r"\bgue\s+os\b", "que os", t, flags=re.I)  # gue os → que os (evitar quebrar "argue")
    t = re.sub(r"abu-\s*tres\b", "abutres", t, flags=re.I)
    t = re.sub(r"tambétn\b", "também", t, flags=re.I)
    t = re.sub(r"c:omo\b", "como", t, flags=re.I)
    t = re.sub(r"alinentam-se", "alimentam-se", t, flags=re.I)
    t = re.sub(r"n1orros\b", "mortos", t, flags=re.I)
    t = re.sub(r"/\\\.+\s*grande", "A grande", t, flags=re.I)
    t = re.sub(r"enconu·ados", "encontrados", t, flags=re.I)
    t = re.sub(r"poden1\b", "podem", t, flags=re.I)
    t = re.sub(r"mesrna\b", "mesma", t, flags=re.I)
    t = re.sub(r"Yítina\b", "vítima", t, flags=re.I)
    t = re.sub(r"vítina\b", "vítima", t, flags=re.I)
    t = re.sub(r"vírina\b", "vítima", t, flags=re.I)
    t = re.sub(r"próxiina\b", "próxima", t, flags=re.I)
    t = re.sub(r"co1no\b", "como", t, flags=re.I)
    t = re.sub(r"co1npri", "compri", t, flags=re.I)  # comprimento
    t = re.sub(r"pottadora\b", "portadora", t, flags=re.I)
    t = re.sub(r"\brnaduras\b", "armaduras", t, flags=re.I)
    t = re.sub(r"\brnanduras\b", "armaduras", t, flags=re.I)
    t = re.sub(r"tnanchbula\b", "mandíbula", t, flags=re.I)
    t = re.sub(r"n1etro\b", "metro", t, flags=re.I)
    t = re.sub(r"anágos\b", "anãos", t, flags=re.I)  # templos anãos
    t = re.sub(r"possuíain\b", "possuíam", t, flags=re.I)
    t = re.sub(r"peranbulan1\b", "perambulam", t, flags=re.I)
    t = re.sub(r"estejan1\b", "estejam", t, flags=re.I)
    t = re.sub(r"adiantan1\b", "adiantam", t, flags=re.I)
    t = re.sub(r"l\\Iágica\b", "Mágica", t, flags=re.I)
    t = re.sub(r"l\\\\Iágica\b", "Mágica", t, flags=re.I)
    t = re.sub(r"\blmortal\b", "Imortal", t, flags=re.I)
    t = re.sub(r"nh a min ú s cuia", "é uma minúscula", t, flags=re.I)
    t = re.sub(r"i\s*a·?\s*_\s*portadora", "é portadora", t, flags=re.I)
    t = re.sub(r"comprin1ento\b", "comprimento", t, flags=re.I)
    t = re.sub(r"mas i:\s*ão causa", "mas é portadora de um veneno extremamente poderoso: sua picada não causa", t, flags=re.I)
    t = re.sub(r"\brrnaduras\b", "Armaduras", t, flags=re.I)
    t = re.sub(r"n1orra\b", "morta", t, flags=re.I)
    t = re.sub(r"centúnetros\b", "centímetros", t, flags=re.I)
    t = re.sub(r"compr\.\s*rinento\b", "comprimento", t, flags=re.I)
    t = re.sub(r"n1adeira\b", "madeira", t, flags=re.I)
    t = re.sub(r"\s+d e\s+", " de ", t, flags=re.I)  # "1 cm d e diâmetro" -> "1 cm de diâmetro"
    t = re.sub(r"\bmn Teste\b", "um Teste", t, flags=re.I)
    t = re.sub(r"compr\.\s*rinento", "comprimento", t, flags=re.I)
    t = re.sub(r"compr\.\s*comprimento", "comprimento", t, flags=re.I)  # correção de duplicação
    t = re.sub(r"\brinento e sua mordida\b", "comprimento e sua mordida", t, flags=re.I)
    t = re.sub(r",\s*mas i:\s*$", "", t, flags=re.I)  # remove "mas i:" truncado no final
    t = re.sub(r"carnh·oros", "carnívoros", t, flags=re.I)
    t = re.sub(r"eternanente\b", "eternamente", t, flags=re.I)
    t = re.sub(r"transfonnando", "transformando", t, flags=re.I)
    t = re.sub(r"tvfuiros\b", "Muitos", t, flags=re.I)
    t = re.sub(r"uni\.\s*idade\b", "umidade", t, flags=re.I)
    t = re.sub(r"movinenraÇão\b", "movimentação", t, flags=re.I)
    t = re.sub(r"po-\s*den1\b", "podem", t, flags=re.I)
    t = re.sub(r"po-\s*dem\b", "podem", t, flags=re.I)
    t = re.sub(r"mo\.rtos", "mortos", t, flags=re.I)
    t = re.sub(r"ura de l\\:?Iedo", "aura de Medo", t, flags=re.I)
    t = re.sub(r"L\\.íagias", "Magias", t, flags=re.I)
    t = re.sub(r"\.lé1n\b", "Além", t, flags=re.I)
    t = re.sub(r"conseguen1\b", "conseguem", t, flags=re.I)
    t = re.sub(r"n1ortos-vivos", "mortos-vivos", t, flags=re.I)
    t = re.sub(r"n1esmo\b", "mesmo", t, flags=re.I)
    t = re.sub(r"l\\íagia\b", "Magia", t, flags=re.I)
    t = re.sub(r"arnas\s+n1ágicas", "armas mágicas", t, flags=re.I)
    t = re.sub(r"possan1\b", "possam", t, flags=re.I)
    t = re.sub(r"escassear·esse", "escassear esse", t, flags=re.I)
    t = re.sub(r"atacan1\b", "atacam", t, flags=re.I)
    t = re.sub(r"rananho\b", "tamanho", t, flags=re.I)
    t = re.sub(r"111011stro\b", "monstro", t, flags=re.I)
    t = re.sub(r"\.GI\b", " AGI", t, flags=re.I)
    t = re.sub(r"#tagues\b", "#Ataques", t, flags=re.I)
    t = re.sub(r"\(\]ucotada", "Coçada", t, flags=re.I)
    t = re.sub(r"Gi\\l'\\JHE\b", "GANHE", t, flags=re.I)
    t = re.sub(r"Cl\s*:RA\s*R\b", "cravá", t, flags=re.I)  # CRAVAR/cravá
    # Avatares e similares (Guia Arton)
    t = re.sub(r"i\\taque\b", "Ataque", t, flags=re.I)
    t = re.sub(r"\\lorpal\b", "Mortal", t, flags=re.I)
    t = re.sub(r"\bforna\b", "forma", t, flags=re.I)
    t = re.sub(r"\bforn1a\b", "forma", t, flags=re.I)
    t = re.sub(r"n1undo\b", "mundo", t, flags=re.I)
    t = re.sub(r"n1enores\b", "menores", t, flags=re.I)
    t = re.sub(r"J\\\s*aparência", "A aparência", t, flags=re.I)
    t = re.sub(r"co-\s*mun1\b", "comum", t, flags=re.I)
    t = re.sub(r"n1eios\b", "meios", t, flags=re.I)
    t = re.sub(r"\brneios\b", "meios", t, flags=re.I)
    t = re.sub(r"\bn1enos\b", "menos", t, flags=re.I)
    t = re.sub(r"assin1\b", "assim", t, flags=re.I)
    t = re.sub(r"vatt'lres\b", "Avatares", t, flags=re.I)
    t = re.sub(r"\bsào\b", "são", t, flags=re.I)
    t = re.sub(r"\blnortal\b", "Imortal", t, flags=re.I)
    t = re.sub(r"\bln1ortal\b", "Imortal", t, flags=re.I)
    t = re.sub(r"Canúnhos\b", "Caminhos", t, flags=re.I)
    t = re.sub(r"Cru11inhos\b", "Caminhos", t, flags=re.I)
    t = re.sub(r"consonem\b", "consomem", t, flags=re.I)
    t = re.sub(r"conson1em\b", "consomem", t, flags=re.I)
    t = re.sub(r"n1ágicos\b", "mágicos", t, flags=re.I)
    t = re.sub(r"\butna\b", "uma", t, flags=re.I)
    t = re.sub(r"\b1nais\b", "mais", t, flags=re.I)
    t = re.sub(r"\bu1n\b", "um", t, flags=re.I)
    t = re.sub(r"í111une\b", "imune", t, flags=re.I)
    t = re.sub(r"\barnas\b", "armas", t, flags=re.I)
    # Magia (variantes OCR)
    t = re.sub(r"l\\iagia", "Magia", t, flags=re.I)
    t = re.sub(r"I\\Jagia", "Magia", t, flags=re.I)
    t = re.sub(r"psiquisn10\b", "psiquismo", t, flags=re.I)
    t = re.sub(r"^cial\s", "Especial ", t)

    # Padrões genéricos
    t = re.sub(r"1\s*\\\s*", "", t)
    t = re.sub(r"~", "", t)
    t = re.sub(r"con1prar", "comprar", t, flags=re.I)
    t = re.sub(r"perden1|perdem1", "perdem", t, flags=re.I)
    t = re.sub(r"nunc:a|nunca\s*:", "nunca", t, flags=re.I)
    t = re.sub(r"catacu1nbas", "catacumbas", t, flags=re.I)
    # n1 → n (exceto em palavras já corrigidas e em números)
    t = re.sub(r"([a-záéíóúâêôãõ])n1([a-záéíóúâêôãõ])", r"\1n\2", t, flags=re.I)
    # fo1 → for em palavras comuns
    t = re.sub(r"fo1([a-záéíóúâêôãõ]{2,})", r"for\1", t, flags=re.I)

    # Limpeza agressiva: números, stats garbled
    t = re.sub(r"(\d+)-1\s+5\b", r"\1-15", t)
    t = re.sub(r"(\d+)-1\s+(\d)\b", r"\1-1\2", t)
    t = re.sub(r"\bII\s+TO\b", "AGI", t, flags=re.I)
    t = re.sub(r"\bDE\s+XO\b", "DEX 0", t, flags=re.I)
    t = re.sub(r"\bPE\s+R\b", "PER", t, flags=re.I)
    t = re.sub(r"\bFR\s+S-", "FR 5-", t, flags=re.I)
    t = re.sub(r"['\"]+\.\)?ú111\s*", "Só ", t, flags=re.I)
    t = re.sub(r"#!?[\s\\]+taques", "#Ataques", t, flags=re.I)
    t = re.sub(r"#!?[\s\\]+aques", "#Ataques", t, flags=re.I)
    t = re.sub(r"(\d+)°10\b", r"\1%", t)
    t = re.sub(r"\bli\s+F(\d)", r" F\1", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t)

    return t


def normalizar_texto_legivel(texto: str) -> str:
    """
    Aplica normalizar_ocr e melhora legibilidade (espaços, hifenização).
    Para descrições de monstros e outros textos extraídos de PDF.
    """
    if not texto or not isinstance(texto, str):
        return texto
    t = normalizar_ocr(texto)
    # Hifenização quebrada: "palavra- ra" -> "palavra"
    t = re.sub(r"(\w)-\s+", r"\1", t)
    # Múltiplos espaços
    t = re.sub(r" +", " ", t)
    # Espaço após pontuação antes de letra
    t = re.sub(r"([.!?,;:])([A-Za-zÀ-ÿ])", r"\1 \2", t)
    # Remove espaço antes de pontuação
    t = re.sub(r" +([.,;:!?])", r"\1", t)
    return t.strip()
