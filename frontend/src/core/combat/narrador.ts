import type {
  EstadoBatalha,
  ResultadoAtaque,
  MensagemMestre,
  LadoBatalha,
} from "./types";

function gerarIdMensagem(): string {
  return `m-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function nomeLado(estado: EstadoBatalha, lado: LadoBatalha): string {
  return lado === "jogador" ? estado.jogador.nome : estado.monstro.nome;
}

export function narrarInicioBatalha(
  estado: EstadoBatalha
): MensagemMestre {
  const texto =
    `🎲 O combate começa! ${estado.jogador.nome} encara ${estado.monstro.nome} ` +
    `em um duelo digno de 3D&T. Boa sorte aos dois!`;
  return {
    id: gerarIdMensagem(),
    autor: "mestre",
    texto,
    timestamp: Date.now(),
  };
}

export function narrarAtaque(
  estado: EstadoBatalha,
  resultado: ResultadoAtaque
): MensagemMestre {
  const atacanteNome = nomeLado(estado, resultado.atacante);
  const alvoNome = nomeLado(estado, resultado.alvo);

  const tipoDescricao =
    resultado.tipo === "ataque_corpo_a_corpo"
      ? "ataque corpo a corpo"
      : resultado.tipo === "ataque_distancia"
      ? "ataque à distância"
      : resultado.tipo === "magia" && resultado.descricaoAcao
      ? `magia ${resultado.descricaoAcao}`
      : "ação";

  const textoBase =
    `⚔️ ${atacanteNome} parte para o ${tipoDescricao}! ` +
    `FA ⚔️ ${resultado.fa.total} (1d6=${resultado.fa.d6}) vs FD 🛡️ ${resultado.fd.total} (1d6=${resultado.fd.d6}). `;

  const textoResultado = resultado.acertou
    ? `💥 O golpe acerta em cheio, causando ${resultado.dano} de dano em ${alvoNome} (PV ${resultado.pvAlvoAntes} → ${resultado.pvAlvoDepois}).`
    : `🛡️ ${alvoNome} se defende ou sai do caminho no último instante — nenhum dano é sofrido.`;

  return {
    id: gerarIdMensagem(),
    autor: "mestre",
    texto: textoBase + textoResultado,
    timestamp: Date.now(),
  };
}

export function narrarFimBatalha(
  estado: EstadoBatalha
): MensagemMestre {
  if (!estado.encerrada || !estado.vencedor) {
    return {
      id: gerarIdMensagem(),
      autor: "mestre",
      texto: "⏳ A batalha continua sem vencedor definido. Preparem o próximo lance!",
      timestamp: Date.now(),
    };
  }

  const vencedorNome = nomeLado(estado, estado.vencedor);
  const perdedorNome =
    estado.vencedor === "jogador"
      ? estado.monstro.nome
      : estado.jogador.nome;

  const texto =
    `🏁 A batalha chega ao fim. ${vencedorNome} permanece de pé, ` +
    `enquanto ${perdedorNome} cai derrotado. 🎲 O dado decidiu, sem favorecer ninguém.`;

  return {
    id: gerarIdMensagem(),
    autor: "mestre",
    texto,
    timestamp: Date.now(),
  };
}

