import { create } from "zustand";
import type { FichaPersonagem } from "@/types/personagem";
import type { Monstro } from "@/types/monstro";
import { usePersonagensStore } from "@/store/personagensStore";
import {
  type EstadoBatalha,
  type MensagemMestre,
  type AcaoJogador,
} from "@/core/combat/types";
import { inicializarBatalhaSimples, resolverAtaque } from "@/core/combat/engine";
import { decidirAcaoMonstro } from "@/core/combat/agenteMonstro";
import { narrarInicioBatalha, narrarAtaque, narrarFimBatalha } from "@/core/combat/narrador";
import { aplicarModificadoresRaca } from "@/data/racaPacote";
import { obterCustoPmMagia } from "@/core/magiasCombate";
import { calcularForcaMonstro } from "@/core/forcaMonstro";
import { sortearLoot } from "@/core/loot";
import { itensSistema } from "@/data/itens";

function calcularArmaduraExtra(ficha: FichaPersonagem): number {
  let total = 0;
  for (const grupo of ficha.itensPorTipo) {
    if (grupo.tipo !== "Armaduras") continue;
    for (const nome of grupo.itens) {
      const item = itensSistema.find((i) => i.nome === nome);
      if (!item?.bonus) continue;
      const b = item.bonus.trim();
      if (!b || b.startsWith("T$")) continue;
      const matchA = b.match(/A\+?(\d+)/i);
      const matchNum = b.match(/^[+]?(\d+)$/);
      const valorStr =
        (matchA && matchA[1]) || (matchNum && matchNum[1]) || null;
      if (!valorStr) continue;
      const val = parseInt(valorStr, 10);
      if (!Number.isNaN(val)) {
        total += val;
      }
    }
  }
  return total;
}

function construirEstadoJogador(ficha: FichaPersonagem): EstadoBatalha["jogador"] {
  const caracEfetivas = aplicarModificadoresRaca(
    ficha.caracteristicas,
    ficha.raca
  );
  const armaduraExtra = calcularArmaduraExtra(ficha);
  const itensEquipados = ficha.itensPorTipo.flatMap((g) => g.itens);
  return {
    tipo: "jogador",
    nome: ficha.nome || "Herói",
    F: caracEfetivas.F ?? 0,
    H: caracEfetivas.H ?? 0,
    R: caracEfetivas.R ?? 0,
    A: (caracEfetivas.A ?? 0) + armaduraExtra,
    PdF: caracEfetivas.PdF ?? 0,
    pvMax: ficha.pvMax,
    pvAtual: ficha.pvAtual,
    pmMax: ficha.pmMax,
    pmAtual: ficha.pmAtual,
    experiencia: ficha.experiencia,
    magiasConhecidas: [...ficha.magiasConhecidas],
    tipoDanoForca: ficha.tiposDano.Força,
    tipoDanoPdF: ficha.tiposDano["Poder de Fogo"],
    itensEquipados,
  };
}

function construirEstadoMonstro(monstro: Monstro): EstadoBatalha["monstro"] {
  const c = monstro.caracteristicas || {};
  const parse = (v: string | undefined) => {
    if (!v) return 0;
    const n = parseInt(v.trim(), 10);
    return Number.isNaN(n) ? 0 : n;
  };
  const parseRecurso = (v: string | undefined) => {
    if (!v) return 1;
    const n = parseInt(v.trim(), 10);
    return Number.isNaN(n) ? 1 : Math.max(1, n);
  };
  const pv = parseRecurso(monstro.pv);
  const pm = parseRecurso(monstro.pm);

  return {
    tipo: "monstro",
    nome: monstro.nome,
    F: parse(c.F),
    H: parse(c.H),
    R: parse(c.R),
    A: parse(c.A),
    PdF: parse(c.PdF),
    pvMax: pv,
    pvAtual: pv,
    pmMax: pm,
    pmAtual: pm,
  };
}

export type EstadoCombateVisao =
  | { estado: "selecao" }
  | { estado: "em_combate"; batalha: EstadoBatalha; mensagens: MensagemMestre[] }
  | { estado: "vitoria"; batalha: EstadoBatalha; mensagens: MensagemMestre[] }
  | { estado: "derrota"; batalha: EstadoBatalha; mensagens: MensagemMestre[] };

interface CombatState {
  visao: EstadoCombateVisao;
  monstroSelecionado: Monstro | null;
  setMonstroSelecionado: (monstro: Monstro | null) => void;
  iniciarBatalha: () => void;
  acaoJogador: (acao: AcaoJogador) => void;
  resetar: () => void;
  /** Última rolagem de dado do jogador (1–6) para animação visual */
  ultimoD6Jogador: number | null;
  usarItemMensagem: (nomeItem: string) => void;
}

export const useCombatStore = create<CombatState>((set, get) => ({
  visao: { estado: "selecao" },
  monstroSelecionado: null,
  ultimoD6Jogador: null,

  setMonstroSelecionado: (monstro) => set({ monstroSelecionado: monstro }),

  iniciarBatalha: () => {
    const personagensStore = usePersonagensStore.getState();
    const ativo = personagensStore.getPersonagemAtivo();
    const monstro = get().monstroSelecionado;
    if (!ativo || !monstro) {
      return;
    }
    const jogador = construirEstadoJogador(ativo.ficha);
    const ladoMonstro = construirEstadoMonstro(monstro);
    const batalha = inicializarBatalhaSimples(jogador, ladoMonstro);
    const primeiraMensagem = narrarInicioBatalha(batalha);
    set({
      visao: {
        estado: "em_combate",
        batalha,
        mensagens: [primeiraMensagem],
      },
    });
  },

  usarItemMensagem: (nomeItem) => {
    const estadoAtual = get().visao;
    if (estadoAtual.estado !== "em_combate") return;
    const jogadorNome = estadoAtual.batalha.jogador.nome;
    const msg: MensagemMestre = {
      id: `m-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      autor: "mestre",
      texto: `🎒 ${jogadorNome} escolhe o item "${nomeItem}" na mochila (efeitos em combate ainda serão implementados).`,
      timestamp: Date.now(),
    };
    set({
      visao: {
        ...estadoAtual,
        mensagens: [...estadoAtual.mensagens, msg],
      },
    });
  },

  acaoJogador: (acao) => {
    const estadoAtual = get().visao;
    if (estadoAtual.estado !== "em_combate") return;
    if (estadoAtual.batalha.turnoDe !== "jogador") return;
    let batalhaBase: EstadoBatalha = estadoAtual.batalha;

    if (acao.tipo === "magia") {
      const nomeMagia = acao.magiaNome ?? "";
      const custoPm = obterCustoPmMagia(nomeMagia);
      const pmAtual = batalhaBase.jogador.pmAtual;
      if (pmAtual < custoPm) {
        const msgSemPm: MensagemMestre = {
          id: `m-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          autor: "mestre",
          texto: `💤 ${batalhaBase.jogador.nome} tenta lançar ${nomeMagia}, mas não tem PM suficientes (precisa de ${custoPm}, tem ${pmAtual}).`,
          timestamp: Date.now(),
        };
        set({
          visao: {
            ...estadoAtual,
            mensagens: [...estadoAtual.mensagens, msgSemPm],
          },
        });
        return;
      }
      batalhaBase = {
        ...batalhaBase,
        jogador: {
          ...batalhaBase.jogador,
          pmAtual: pmAtual - custoPm,
        },
      };
    }

    const { estado: estadoAposJogador, resultado } = resolverAtaque(
      batalhaBase,
      acao
    );
    if (acao.lado === "jogador") {
      set({ ultimoD6Jogador: resultado.fa.d6 });
    }
    const msgJogador = narrarAtaque(estadoAposJogador, resultado);
    let mensagens = [...estadoAtual.mensagens, msgJogador];

    if (estadoAposJogador.encerrada) {
      let batalhaFinal = estadoAposJogador;
      if (estadoAposJogador.vencedor === "jogador") {
        const monstroSel = get().monstroSelecionado;
        const forca = monstroSel ? calcularForcaMonstro(monstroSel) : 0;
        const xpGanho = Math.max(1, 10 + Math.round(forca / 2));
        batalhaFinal = {
          ...estadoAposJogador,
          jogador: {
            ...estadoAposJogador.jogador,
            experiencia: estadoAposJogador.jogador.experiencia + xpGanho,
          },
        };
        const personagensStore = usePersonagensStore.getState();
        const ativo = personagensStore.getPersonagemAtivo();
        if (ativo) {
          personagensStore.updatePersonagem(ativo.id, {
            ...ativo.ficha,
            experiencia: ativo.ficha.experiencia + xpGanho,
          });
        }
        const loot = monstroSel ? sortearLoot(monstroSel) : [];
        const lootTexto =
          loot.length > 0
            ? loot.map((l) => l.descricao).join("; ")
            : "nenhum loot caiu desta vez";
        const recompensaMsg: MensagemMestre = {
          id: `m-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          autor: "mestre",
          texto: `🏆 Recompensa: +${xpGanho} XP! 💰 Loot: ${lootTexto}.`,
          timestamp: Date.now(),
        };
        mensagens = [...mensagens, recompensaMsg];
      }
      const fim = narrarFimBatalha(batalhaFinal);
      mensagens = [...mensagens, fim];
      set({
        visao: {
          estado:
            batalhaFinal.vencedor === "jogador" ? "vitoria" : "derrota",
          batalha: batalhaFinal,
          mensagens,
        },
      });
      return;
    }

    const monstroSelecionado = get().monstroSelecionado;
    if (!monstroSelecionado) {
      set({
        visao: {
          estado: "em_combate",
          batalha: estadoAposJogador,
          mensagens,
        },
      });
      return;
    }

    const acaoMonstro = decidirAcaoMonstro(
      estadoAposJogador,
      monstroSelecionado
    );
    const { estado: estadoAposMonstro, resultado: resultadoMonstro } =
      resolverAtaque(estadoAposJogador, acaoMonstro);
    const msgMonstro = narrarAtaque(estadoAposMonstro, resultadoMonstro);
    mensagens = [...mensagens, msgMonstro];

    if (estadoAposMonstro.encerrada) {
      let batalhaFinal = estadoAposMonstro;
      if (estadoAposMonstro.vencedor === "jogador") {
        const monstroSel = get().monstroSelecionado;
        const forca = monstroSel ? calcularForcaMonstro(monstroSel) : 0;
        const xpGanho = Math.max(1, 10 + Math.round(forca / 2));
        batalhaFinal = {
          ...estadoAposMonstro,
          jogador: {
            ...estadoAposMonstro.jogador,
            experiencia: estadoAposMonstro.jogador.experiencia + xpGanho,
          },
        };
        const personagensStore = usePersonagensStore.getState();
        const ativo = personagensStore.getPersonagemAtivo();
        if (ativo) {
          personagensStore.updatePersonagem(ativo.id, {
            ...ativo.ficha,
            experiencia: ativo.ficha.experiencia + xpGanho,
          });
        }
        const loot = monstroSel ? sortearLoot(monstroSel) : [];
        const lootTexto =
          loot.length > 0
            ? loot.map((l) => l.descricao).join("; ")
            : "nenhum loot caiu desta vez";
        const recompensaMsg: MensagemMestre = {
          id: `m-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          autor: "mestre",
          texto: `🏆 Recompensa: +${xpGanho} XP! 💰 Loot: ${lootTexto}.`,
          timestamp: Date.now(),
        };
        mensagens = [...mensagens, recompensaMsg];
      }
      const fim = narrarFimBatalha(batalhaFinal);
      mensagens = [...mensagens, fim];
      set({
        visao: {
          estado:
            batalhaFinal.vencedor === "jogador" ? "vitoria" : "derrota",
          batalha: batalhaFinal,
          mensagens,
        },
      });
      return;
    }

    set({
      visao: {
        estado: "em_combate",
        batalha: estadoAposMonstro,
        mensagens,
      },
    });
  },

  resetar: () =>
    set({
      visao: { estado: "selecao" },
      monstroSelecionado: null,
    }),
}));

