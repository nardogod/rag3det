"""
Enriquecimento de descrição de monstros: extrai campos estruturados da descrição.
Campos: comportamento, altura_tamanho, peso, habitat, comportamento_dia_noite,
        comportamento_combate, habilidades (além das mecânicas).

Piloto: 5 monstros do Livro de Arton (Daemon).
Executar: python scripts/enriquecer_descricao_monstros.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Piloto: dados enriquecidos extraídos manualmente das descrições do Guia Daemon
PILOTO_ARTON: dict[str, dict[str, Any]] = {
    "Abelha-Gigante": {
        "comportamento": "Obedecem hierarquia de colmeia, como abelhas normais. Podem ser cavalgadas por criaturas de tamanho humano ou menor. Larvas alimentadas com mel tornam-se leais a quem as criou.",
        "altura_tamanho": "Tamanho aproximado de um grande felino. Forma de inseto com seis patas; caminha sobre as quatro traseiras, patas dianteiras recolhidas na base do pescoço.",
        "peso": "Não especificado",
        "habitat": "Grandes campos floridos; colmeia em caverna próxima. Uma colmeia abriga 5d zangões e operárias, mais uma rainha.",
        "comportamento_dia_noite": "Diurnas: passam o dia colhendo pólen nos campos floridos.",
        "comportamento_combate": "Agarram presa com patas dianteiras (não causa dano, apenas prende). Enquanto presa, vítima recebe mordida por turno (a abelha acerta automaticamente). Ferrão no abdome como último recurso — perde o ferrão e morre horas depois. Usam ataque terrível só em extremo perigo.",
        "habilidades_extra": "Levitação; veneno no ferrão (Teste de R+1, falha=morte, sucesso=3d6 dano ignorando Armadura). Mel produzido tem propriedades curativas (1 litro recupera 1d PVs).",
    },
    "Ameba-Gigante": {
        "comportamento": "Criatura unicelular, quase inteiramente feita de líquido. Citoplasma gelatinoso e ácido contido por membrana. Núcleo flutua no centro.",
        "altura_tamanho": "10 m de diâmetro. Núcleo: esfera de 0,5 m de diâmetro no centro.",
        "peso": "Não especificado (corpo líquido/gelatinoso)",
        "habitat": "Não especificado no trecho (subterrâneos, áreas úmidas típicas para amebas gelatinosas)",
        "comportamento_dia_noite": "Não especificado",
        "comportamento_combate": "Até quatro ataques por turno com pseudópodes (tentáculos projetados). Invulnerável a Contusão, Corte, Perfuração, Químico. Vulnerável a Calor/Fogo.",
        "habilidades_extra": "Invulnerabilidade a armas e ácido; Vulnerabilidade a Calor/Fogo.",
    },
    "Asa Negra": {
        "comportamento": "Magníficas águias. Muito procuradas por nobres e caçadores para falcoaria. Difícil treinar quando adultas; nobreza paga grandes quantias por ovos. Treinadas desde nascimento tornam-se excelentes companheiras.",
        "altura_tamanho": "Tamanho de águia.",
        "peso": "Não especificado",
        "habitat": "Montanhas mais inacessíveis e perigosas de Arton. Constroem ninhos em locais de difícil acesso.",
        "comportamento_dia_noite": "Plumagem totalmente negra; torna-se quase invisível durante a noite.",
        "comportamento_combate": "Não é agressiva por natureza. Usada em falcoaria para caça e competições. Se atacada, defende-se com bico e garras.",
        "habilidades_extra": "Sentidos Especiais; Levitação. Quase invisível à noite.",
    },
    "Asfixor": {
        "comportamento": "Lesma gigante predadora. Pode mudar de cor e ficar quase invisível quando rasteja por masmorras abandonadas.",
        "altura_tamanho": "Até 5 m de comprimento.",
        "peso": "Não especificado",
        "habitat": "Masmorras abandonadas, subterrâneos.",
        "comportamento_dia_noite": "Ambientes escuros; prefere tetos e chão de masmorras. Não depende de ciclo dia/noite.",
        "comportamento_combate": "Grudado no teto, espera vítimas passarem por baixo e se deixa cair; ou estendido no chão, esperando alguém pisar. Ao cair ou se erguer, ataque acerta automaticamente (sem testes). Fecha com força à volta da vítima, sufocando (1d6 dano/rodada, ignora Armadura). Vítima aprisionada: só ataca com Teste de Força; armas pequenas, dano máx 1d6. Ataques de terceiros no monstro causam metade do dano na vítima.",
        "habilidades_extra": "Ataque automático ao cair/erguer; sufocação; mudança de cor (quase invisível).",
    },
    "Gondo": {
        "comportamento": "Fera monstrosa criada magicamente por antigo feiticeiro. Caçador noturno que devora o que puder agarrar. Muito difícil perceber sua aproximação: Teste de Percepção (H-2 ou H-3) para detectá-lo antes do ataque surpresa; ou H+1 com Sentidos Especiais (Audição Aguçada, Faro) para sentir os leves tremores de terra provocados por seus passos.",
        "altura_tamanho": "Aproximadamente 3 m de altura. Postura inclinada como troglodita. Cara de gorila com orelhas humanas; chifres longos retorcidos (cabrito-montês). Dois dedos e polegar em cada mão com garras. Pés como patas de macaco.",
        "peso": "Não menos de 300 kg",
        "habitat": "Perambula pela escuridão. Não especificado (florestas, ruínas, áreas selvagens).",
        "comportamento_dia_noite": "Noturno: perambula pela escuridão. Durante o dia geralmente dorme em cavernas. Qualquer ação diurna provoca redutor -1; exposto ao sol: redutor -3 e tenta fugir.",
        "comportamento_combate": "Três ataques por turno: duas garras e mordida. Pode atacar com chifres (prefere contra outros machos). Corrida + chifres causa dano dobrado. Gera aura mágica que camufla corpo com a noite (invisível). Não produz ruído; apenas leves tremores de terra nos passos.",
        "habilidades_extra": "Invisibilidade (apenas à noite); couro muito resistente.",
    },
    # Novos 5 monstros para avaliação
    "Basilisco": {
        "comportamento": "Grande lagarto esguio. Péssimo lutador corporal, mas possui poder mágico de petrificação por contato visual. Evita combate direto quando possível.",
        "altura_tamanho": "Quase 2 m de comprimento (1 m de cauda). Escamas verde brilhante, crista azulada atrás da cabeça. Patas com dedos ligados por membranas. Olhos grandes e amarelos.",
        "peso": "Não especificado",
        "habitat": "Áreas úmidas, pântanos, rios (ótimo nadador). Anfíbio.",
        "comportamento_dia_noite": "Não especificado",
        "comportamento_combate": "Usa olhar petrificante (uma vítima por vez). Mordida fraca (1 ponto de dano por turno). Para evitar petrificação: olhos fechados (H-1 corpo, H-3 distância, -10%/-20% esquiva). Vítima faz Teste de Resistência para negar.",
        "habilidades_extra": "Petrificação (contato visual, idêntica à Magia Petrificação; não consome PVs da criatura). Funciona apenas com criaturas vivas.",
    },
    "TIGRE": {
        "comportamento": "Caçador solitário. Prefere atacar em selvas e florestas, matando a presa e levando-a para devorar no alto de uma árvore.",
        "altura_tamanho": "Grande felino. Variedade com pêlo amarelo e manchas escuras (Lamnor). Leopardo-das-neves nas Montanhas Uivantes.",
        "peso": "Não especificado",
        "habitat": "Selvas, florestas. Lamnor (disputa caça com leões). Montanhas Uivantes (leopardo-das-neves).",
        "comportamento_dia_noite": "Não especificado (predador de emboscada, tende a ser crepuscular/noturno)",
        "comportamento_combate": "Até três ataques por turno: duas garras (F-1d) e mordida (F). Grande felino típico 3D&T.",
        "habilidades_extra": "Garras e mordida. Predador de emboscada.",
    },
    "Lobo-das-Cavernas": {
        "comportamento": "Ancestral pré-histórico do lobo. Formam haréns com um macho comandando 5 a 15 fêmeas. Goblins capturam filhotes para treinar como montarias (apenas fêmeas cavalgáveis; machos para guarda e ataque).",
        "altura_tamanho": "Tamanho de lobo. Pelagem cinza-azulada, olhos vermelhos. Fila dorsal de placas ósseas cortantes (apenas machos — atrativo sexual; usadas por tribais para lanças).",
        "peso": "Não especificado",
        "habitat": "Numerosas regiões de Arton, especialmente Galrasia. Florestas, cavernas, vales profundos.",
        "comportamento_dia_noite": "Não especificado",
        "comportamento_combate": "Ataca em matilha. Mordida e possivelmente placas. Usado por goblins como montaria ou guarda.",
        "habilidades_extra": "Sentidos Especiais (Audição Aguçada, Faro). Placas dorsais nos machos.",
    },
    "Centopéia-Gigante": {
        "comportamento": "Sempre faminta; ataca qualquer coisa à vista. Criatura solitária. Matar uma sozinha é rito de passagem das dragão-caçadoras de Galrasia.",
        "altura_tamanho": "Mais de 8 m de comprimento, até 1 m de largura e 30 cm de altura. Maioria tem metade desse tamanho.",
        "peso": "Não especificado",
        "habitat": "Lugares escondidos: florestas, selvas, pântanos, cavernas, vales profundos — longe da luz do sol. Algumas espécies ativas dia e noite.",
        "comportamento_dia_noite": "Prefere escuridão. Algumas espécies ativas dia e noite.",
        "comportamento_combate": "Mordida causa dano por Força + veneno. Vítima: Teste de R ou sofre 1d6 dano extra e redutor -1 em todos os testes por horas (sucesso: -1 por meia hora).",
        "habilidades_extra": "Veneno (3d6 dano; falha em R: +1d6 e redutor -1 por horas).",
    },
    "Corcel das Trevas": {
        "comportamento": "Morto-vivo poderoso, criação de Tenebra. Oferecido como montaria aos servos mais devotados. Vampiros, Liches e clérigos das trevas cavalgam.",
        "altura_tamanho": "Aspecto de grande cavalo negro com olhos vermelhos e brilhantes.",
        "peso": "Não especificado",
        "habitat": "Onde servos das trevas o utilizam. Não é criatura natural.",
        "comportamento_dia_noite": "Morto-vivo; associado à escuridão.",
        "comportamento_combate": "Possui poderes de morto-vivo. Imune a venenos, doenças, magias/poderes que afetam mente e coisas que só funcionam contra vivos. Magias de cura causam dano. Recupera PVs com descanso ou Magia Cura para os Mortos. Nunca ressuscitado.",
        "habilidades_extra": "Aceleração; Levitação. Imunidades de morto-vivo.",
    },
}


def enriquecer_monstro(monstro: dict[str, Any], dados: dict[str, Any]) -> dict[str, Any]:
    """Adiciona campos enriquecidos ao monstro."""
    out = dict(monstro)
    for k, v in dados.items():
        out[k] = v
    return out


def aplicar_piloto_arton(main_path: Path) -> int:
    """
    Aplica os dados do piloto aos 5 monstros do Livro de Arton no ecossistema.
    Retorna quantidade de monstros enriquecidos.
    """
    livro_daemon = "tormenta daemon guia de monstros de arton biblioteca elfica"

    if not main_path.exists():
        return 0

    data = json.loads(main_path.read_text(encoding="utf-8"))
    count = 0

    for m in data:
        if (m.get("livro") or "").lower() != livro_daemon:
            continue
        nome = m.get("nome")
        if nome and nome in PILOTO_ARTON:
            dados = PILOTO_ARTON[nome]
            for k, v in dados.items():
                m[k] = v
            count += 1

    if count > 0:
        with main_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return count


def main() -> None:
    out_dir = Path("data/processed/monstros")
    main_path = out_dir / "monstros_extraidos.json"

    print("Enriquecendo descrição de monstros (piloto: 10 do Livro de Arton)...")
    count = aplicar_piloto_arton(main_path)
    print(f"[OK] {count} monstros enriquecidos em {main_path}")


if __name__ == "__main__":
    main()
