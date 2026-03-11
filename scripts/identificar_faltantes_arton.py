"""
Identifica criaturas faltantes no Livro de Arton.
Compara o índice de referência com os monstros extraídos e lista os que faltam.

Executar: python scripts/identificar_faltantes_arton.py
Saída: data/processed/monstros/faltantes_arton.json e relatório no console
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Aliases: nomes no PDF podem diferir do índice (OCR, variações)
ALIASES_INDICE: dict[str, list[str]] = {
    "Feras-Caçus": ["Feras-Cactus", "Feras Cactus"],
    "Fil-Gikin": ["Fil-Gikim", "Fil Gikim"],
    "Devoradores": ["Devorador do Deserto", "Devorador de Ouro", "Devorador"],
}

# Índice de criaturas do Guia de Monstros de Arton (docs/ANALISE_GUIA_DAEMON)
INDICE_ARTON = [
    "Abelha-Gigante", "Água-Viva", "Ameba-Gigante", "Anões", "Aparições",
    "Aranhas-Gigantes", "Arraia", "Asa-Assassina", "Asa-Negra", "Asflor",
    "Assassino da Savana", "Assustador", "Avatares", "Baleias", "Banshee",
    "Basilisco", "Beijo-de-Tenebra", "Besouros", "Brownies", "Bruxas",
    "Canários-do-Sono", "Caoceronte", "Carniceiros", "Carrasco de Lena",
    "Cavalos", "Centauro", "Centopéia-Gigante", "Ceratops", "Cocatriz",
    "Colosso da Tormenta", "Composognato", "Corcel do Deserto", "Corcel das Trevas",
    "Couatl", "Crocodilos", "Demônios", "Devoradores", "Diabo-de-Keenn",
    "Dimmak", "Dinonico", "Dionys", "Dragões", "Dríade", "Duplo",
    "Elefantes", "Elementais", "Elfos", "Enfermeiras", "Entes", "Esfinge",
    "Esqueletos", "Familiares", "Fantasma", "Fênix", "Feras-Caçus", "Fil-Gikin",
    "Fofo", "Fogo-Fátuo", "Formigas-Hiena", "Fungi", "Gafanhoto-Tigre",
    "Gambá", "Gárgula", "Gênios", "Ghoul", "Gigantes", "Gnolls",
    "Goblinóides", "Golens", "Golfinho", "Gondo", "Górgon", "Grama Carnívora",
    "Grandes Felinos", "Grandes Símios", "Grifo", "Guerreiro da Luz",
    "Halflings", "Harpia", "Hidra", "Hipogrifo", "Homens-Escorpião",
    "Homens-Lagarto", "Homens-Morcego", "Homens-Serpente", "Homúnculo",
    "Horror dos Túmulos", "Ictiossauro", "Incubador", "Kaatar-nirav",
    "Kanatur", "Katrak", "Killbone", "Kobolds", "Kraken", "Leão-de-Keenn",
    "Lesma-Carnívora", "Licantropos", "Lich", "Lobo-das-Cavernas",
    "Mago-Fantasma", "Manticora", "Mortos-Vivos", "Múmia", "Naga",
    "Neblina-Fantasma", "Neblina-Vampírica", "Necrodracos", "Nereida Abissal",
    "Ninfa", "Observadores", "Ogres", "Ores", "Pantera-do-Vidro",
    "Pássaros Arco-Íris", "Pássaros do Caos", "Pégaso", "Peixe-Couraca",
    "Peixe-Gancho", "Peixe-Recife", "Planador", "Povo-Dinossauro", "Povo-Sapo",
    "Predador dos Sonhos", "Predador-Toupeira", "Protocraco", "Pteranodonte",
    "Pteros", "Pudim Negro", "Quelicerossauros", "Quelonte", "Quimera",
    "Random", "Ratazanas", "Serpentes Venenosas", "Siba Gigante", "Sharks",
    "Shimav", "Shinobi", "Soldados-Mortos", "Sprites", "Tahab-krar",
    "Tai-Kanatur", "Tasloi", "Tatu-Aranha", "Tentáculo", "Terizinossauro",
    "Tigre-de-Hyninn", "Toscos", "T-Rex", "Triceratops", "Trilobitas",
    "Trobos", "Trogloditas", "Troll", "Ursos", "Unicórnio", "Vampiro",
    "Varano de Krah", "Velociraptor", "Velocis",
]


def _normalizar(nome: str) -> str:
    """Normaliza nome para comparação (lowercase, sem acentos extras)."""
    return nome.strip().lower().replace("-", " ").replace("  ", " ")


def _nome_similar(nome_indice: str, nome_extraido: str) -> bool:
    """Verifica se nomes são similares (ex.: 'Asa-Negra' vs 'Asa Negra')."""
    a = _normalizar(nome_indice)
    b = _normalizar(nome_extraido)
    if a == b:
        return True
    if a in b or b in a:
        return True
    # Aliases (PDF vs índice): Feras-Cactus↔Feras-Caçus, Fil-Gikim↔Fil-Gikin
    for idx, aliases in ALIASES_INDICE.items():
        if _normalizar(idx) == a:
            if any(_normalizar(al) == b or _normalizar(al) in b for al in aliases):
                return True
        if _normalizar(idx) in a and any(_normalizar(al) == b for al in aliases):
            return True
    # Devoradores: "Devorador do Deserto" cobre "Devoradores"
    if "devorador" in a and "devorador" in b:
        return True
    # Remover prefixos comuns (SOLDADO, XAMÃ, etc.)
    for prefixo in ["soldado ", "arqueiro ", "xamã ", "capitão ", "chefe ", "cavaleiro "]:
        if b.startswith(prefixo) and a in b:
            return True
    return False


def main() -> None:
    path = Path("data/processed/monstros/monstros_extraidos.json")
    if not path.exists():
        print("monstros_extraidos.json não encontrado. Execute a extração primeiro.")
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    livro_arton = "tormenta daemon guia de monstros de arton biblioteca elfica"
    extraidos = [
        m.get("nome", "").strip()
        for m in data
        if (m.get("livro") or "").lower() == livro_arton
    ]
    extraidos_unicos = list(dict.fromkeys(extraidos))  # manter ordem

    # Verificar quais do índice estão cobertos (exato ou similar)
    faltantes: list[str] = []
    cobertos: list[tuple[str, str]] = []  # (indice, extraido)

    for nome in INDICE_ARTON:
        encontrado = False
        for ex in extraidos_unicos:
            if _nome_similar(nome, ex):
                cobertos.append((nome, ex))
                encontrado = True
                break
        if not encontrado:
            faltantes.append(nome)

    # Extraídos que não estão no índice (subvariantes, etc.)
    extraidos_fora_indice = [
        ex for ex in extraidos_unicos
        if not any(_nome_similar(ex, idx) for idx in INDICE_ARTON)
    ]

    out_dir = Path("data/processed/monstros")
    out_dir.mkdir(parents=True, exist_ok=True)
    resultado = {
        "total_indice": len(INDICE_ARTON),
        "total_extraidos": len(extraidos_unicos),
        "faltantes": faltantes,
        "cobertos": [{"indice": a, "extraido": b} for a, b in cobertos],
        "extraidos_fora_indice": extraidos_fora_indice[:50],  # amostra
    }
    out_path = out_dir / "faltantes_arton.json"
    out_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== Criaturas faltantes no Livro de Arton ===\n")
    print(f"Índice de referência: {len(INDICE_ARTON)} criaturas")
    print(f"Extraídas (Arton): {len(extraidos_unicos)}")
    print(f"Faltantes: {len(faltantes)}")
    print(f"\nLista de faltantes:\n{json.dumps(faltantes, ensure_ascii=False, indent=2)}")
    print(f"\n[OK] Detalhes salvos em {out_path}")


if __name__ == "__main__":
    main()
