import type {
  EstadoBatalha,
  AcaoJogador,
  AcaoMonstro,
  ResultadoAtaque,
} from "./types";
import { rolarFA, rolarFD, aplicarDano } from "./formulas";
import type { Monstro } from "@/types/monstro";
import type { TipoDanoForca, TipoDanoPdF } from "@/data/tiposDano";
import { estimarPotenciaMagia } from "../magiasCombate";

export function inicializarBatalhaSimples(
  jogador: EstadoBatalha["jogador"],
  monstro: EstadoBatalha["monstro"]
): EstadoBatalha {
  return {
    jogador,
    monstro,
    turnoDe: "jogador",
    round: 1,
    iniciativaResolvida: true,
    historicoInterno: [],
    encerrada: false,
    vencedor: null,
  };
}

function inferirTipoDano(
  estado: EstadoBatalha,
  acao: AcaoJogador | AcaoMonstro
): string | undefined {
  if (acao.lado === "jogador") {
    const ficha = estado.jogador;
    if (acao.tipo === "ataque_corpo_a_corpo") {
      return (ficha as unknown as { tipoDanoForca?: TipoDanoForca })
        .tipoDanoForca;
    }
    if (acao.tipo === "ataque_distancia" || acao.tipo === "magia") {
      return (ficha as unknown as { tipoDanoPdF?: TipoDanoPdF }).tipoDanoPdF;
    }
  }
  return undefined;
}

function aplicarResistenciasMonstro(
  monstro: Monstro,
  danoBruto: number,
  tipoDano: string | undefined
): number {
  if (danoBruto <= 0) return 0;
  if (!tipoDano) return danoBruto;

  const tipoNorm = tipoDano.toLowerCase();
  const imunes = (monstro.imunidades || []).map((t) => t.toLowerCase());
  const vulner = (monstro.vulnerabilidades || []).map((t) => t.toLowerCase());

  if (imunes.some((t) => tipoNorm.includes(t))) {
    return 0;
  }
  if (vulner.some((t) => tipoNorm.includes(t))) {
    return Math.round(danoBruto * 1.5);
  }
  return danoBruto;
}

export function resolverAtaque(
  estado: EstadoBatalha,
  acao: AcaoJogador | AcaoMonstro
): { estado: EstadoBatalha; resultado: ResultadoAtaque } {
  if (estado.encerrada) {
    return {
      estado,
      resultado: {
        atacante: acao.lado,
        alvo: acao.lado === "jogador" ? "monstro" : "jogador",
        tipo: acao.tipo,
        fa: { d6: 0, total: 0 },
        fd: { d6: 0, total: 0 },
        acertou: false,
        dano: 0,
        pvAlvoAntes: 0,
        pvAlvoDepois: 0,
        descricaoAcao: undefined,
      },
    };
  }

  const atacanteLado = acao.lado;
  const alvoLado = atacanteLado === "jogador" ? "monstro" : "jogador";
  const atacante = atacanteLado === "jogador" ? estado.jogador : estado.monstro;
  const alvo = alvoLado === "jogador" ? estado.jogador : estado.monstro;

  const fa = rolarFA(atacante, acao.tipo);
  const fd = rolarFD(alvo);

  const acertou = fa.total > fd.total;
  const pvAlvoAntes = alvo.pvAtual;

  const danoBase = Math.max(0, fa.total - fd.total);
  let dano = 0;
  if (acertou) {
    if (acao.tipo === "magia" && "magiaNome" in acao && acao.magiaNome) {
      const extra = estimarPotenciaMagia(acao.magiaNome);
      dano = Math.max(1, danoBase + extra);
    } else {
      dano = danoBase;
    }
  }

  const tipoDano = inferirTipoDano(estado, acao);
  let danoFinal = dano;
  if (alvoLado === "monstro" && dano > 0) {
    danoFinal = aplicarResistenciasMonstro(
      (estado.monstro as unknown as Monstro),
      dano,
      tipoDano
    );
  }

  const pvAlvoDepois = aplicarDano(pvAlvoAntes, danoFinal);

  const novoEstado: EstadoBatalha = {
    ...estado,
    jogador:
      alvoLado === "jogador"
        ? { ...estado.jogador, pvAtual: pvAlvoDepois }
        : estado.jogador,
    monstro:
      alvoLado === "monstro"
        ? { ...estado.monstro, pvAtual: pvAlvoDepois }
        : estado.monstro,
    turnoDe: atacanteLado === "jogador" ? "monstro" : "jogador",
  };

  if (pvAlvoDepois <= 0) {
    novoEstado.encerrada = true;
    novoEstado.vencedor = atacanteLado;
  }

  const resultado: ResultadoAtaque = {
    atacante: atacanteLado,
    alvo: alvoLado,
    tipo: acao.tipo,
    fa,
    fd,
    acertou,
    dano: danoFinal,
    pvAlvoAntes,
    pvAlvoDepois,
    descricaoAcao:
      "magiaNome" in acao && acao.magiaNome ? acao.magiaNome : undefined,
    tipoDano,
  };

  return { estado: novoEstado, resultado };
}

