"""
Mapeamento de tipos para os 284 monstros do Manual dos Monstros: Criaturas Fantásticas (revisado).
Baseado no sumário do Manual: Construtos, Feras, Humanoides, Mortos-Vivos, Youkai.
"""

# Construtos (Parte 1)
CONSTRUTOS = frozenset({
    "Caçador", "Caçador de Elite", "Caranguejo de Guerra", "Dínamo da Aliança Negra",
    "Dínamo Atroz do Reino dos Deuses", "Dragão-de-Aço", "Gárgula de Abadia",
    "Golem de Entulho", "Golem-Réplica", "Horror Blindado", "Fado", "Probo", "Parcus",
    "Soldado Mecânico",
})

# Feras (Parte 2)
FERAS = frozenset({
    "Abelha Feral Operária", "Abelha Feral Rainha", "Apis, a Abelha-Imperatriz",
    "Abelha-Grifo Operária", "Abelha-Grifo Guerreira", "Aranha Brutal", "Aranha Brutal Rainha-Mãe",
    "Asa-Assassina", "Asa-Assassina Alfa", "Asa-assassina", "Asa-assassina Alfa",
    "Baleote Selvagem", "Baleote da Milícia de Vectora", "Beijo de Tenebra",
    "Besouro Bestial", "Besouro Bestial Alfa", "Besouro de Azgher", "Enxame de Besouros de Azgher",
    "Bulette Jovem", "Bulette Adulto", "Camelo", "Cão de Guarda com Treinamento de Alerta",
    "Cão de Guarda com Treinamento de Ataque", "Cão de Guarda com Treinamento Físico",
    "Capivara", "Bando de Capivaras", "Cargueiro Adulto", "Cavalo de Carga", "Cavalo de Guerra",
    "Cavalo de Montaria", "Garanhão de Namalkah", "Pônei", "Jumento",
    "Hippion, Deus Menor dos Cavalos", "Cipó Assassino", "Cascavel", "Jiboia", "Naja",
    "Sucuri", "Cobra-Rei", "Crocodilo", "Crocodilo Gigante", "Devorador do Deserto",
    "Dionys", "Elefante", "Elefante da Savana", "Mamute", "Mastodonte", "Escavador",
    "Esmaga-Ossos", "Fera-Cactus", "Fera-Cactus Clérigo da Fera-Mãe", "A Fera-Mãe",
    "Girallon", "Girallon Alfa", "Tatu-Traiçoeiro", "Grama Carnívora", "Grifo Selvagem",
    "Grifo Imperial", "Lagarto Perseguidor", "Lobo", "Lobo-das-Cavernas", "Lobo-das-Neves",
    "Lobo-Rei", "Alcateia do Lobo-Rei", "Mastim de Megalon", "Mastim de Megalon Atroz",
    "Megapeia", "Gigapeia", "Pássaro Roca", "Kuok, a Roca com uma Tribo nas Costas",
    "Peixe-Gancho", "Rã de Sszzaas", "Sapo Atroz", "Inghlblhpholstgt, o Grande Deus-Sapo",
    "Serpente Marinha", "Tentacute", "Tigre Dentes-de-Sabre", "Trobo", "Urso-Coruja",
    "Verme do Gelo", "Verme Púrpura",
})

# Humanoides (Parte 3)
HUMANOIDES = frozenset({
    "Androdraco Guerreiro", "General Androdraco", "Tropa de Sckharshantallas",
    "Dimmak", "Ganchador", "Ganchadora Líder", "Harpia",
    "Daresha, a Caçadora de Keenn", "Daresha, Guerreira Deicida",
    "Homem-Escorpião", "Homem-Peixe Soldado", "Homem-Peixe Capitão", "Homem-Peixe Caçador",
    "Homem-Peixe Clérigo", "Homem-Sapo", "Campeão Batráquio", "Kappa Assaltante",
    "Kappa Que Vive Pela Honra", "Kobold Comum", "Kobold Explosivo", "Kobold Filho do Dragão",
    "Kobold Rei", "Kobold Xamã", "Horda de Kobolds", "Katharmek", "Meio-Zumbi",
    "Oni Vermelho, Verde ou Azul", "Oni Negro",
})

# Mortos-Vivos (Parte 4)
MORTOS_VIVOS = frozenset({
    "Afogado", "Capitão Afogado", "Aparição", "Banshee", "Bodak", "Carniçal", "Lacedon", "Lívido",
    "Cemitério Vivo", "Demônio das Sombras", "Homúnculo", "Inumano", "General Inumano",
    "Tropa de Inumanos", "Mortos-Vivos", "Horda de Mortos-Vivos", "Necrodraco", "Dragão-Esqueleto",
    "Dragão-Zumbi", "Dracolich", "Tarso, o Rei dos Dragões-Lich", "Pileus Estágio Um",
    "Pileus Estágio Dois", "Pileus Estágio Três", "Soldado Múltiplo", "Verme Fantasma",
})

# Youkai (Parte 5) - resto
# Inclui: Aboleth, Ameba Gigante, Asfixor, Canário-do-Sono, Carrasco de Lena, Catoblepas,
# Coatl, Cocatriz, Criatura da Poluição, Criatura Ocular, Damaru, Dragões, Elementais,
# Escolhido dos Deuses, Espírito da Terra, Fênix, Fera Negra, Fogo-Fátuo, Hidra,
# Horror dos Túmulos, Incubador, Lagarto Elétrico, Magnetus, Mantícora, Mímico, Taklit,
# Monstro da Ferrugem, Naga, Ninfa, Orquídea Carnívora, Paraelemental, Pirâmide Gelatinosa,
# Predador do Lixo, Quimera, Serpente dos Sonhos, Skum, Thoqqua, Tirano Ocular, Ko'z,
# Troll, Wyvern, etc.


def obter_tipo_manual(nome: str) -> str:
    """Retorna o tipo do monstro conforme o Manual dos Monstros: Criaturas Fantásticas."""
    if nome in CONSTRUTOS:
        return "construto"
    if nome in FERAS:
        return "besta"
    if nome in HUMANOIDES:
        return "humanóide"
    if nome in MORTOS_VIVOS:
        return "morto-vivo"
    # Youkai e demais (dragões, elementais, etc.)
    return "espírito"
