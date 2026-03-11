/**
 * Estado global da Ficha de Personagem (Zustand).
 * Baseado no Manual 3D&T Turbinado Digital, p. 144.
 */

import { create } from "zustand";
import type {
  FichaPersonagem,
  CaracteristicaKey,
  CaminhoMagia,
  NivelPontuacao,
} from "@/types/personagem";
import { FICHA_INICIAL } from "@/types/personagem";
import { MAX_CARAC_FOCUS } from "@/core/construcaoPersonagem";
import { RACA_EXCLUI_VANTAGEM, RACA_EXCLUI_DESVANTAGEM } from "@/core/dependencias";

interface PersonagemState extends FichaPersonagem {
  setNivelPontuacao: (nivel: NivelPontuacao) => void;
  setRaca: (raca: string | null) => void;
  addVantagem: (nome: string) => void;
  removeVantagem: (nome: string) => void;
  addDesvantagem: (nome: string) => void;
  removeDesvantagem: (nome: string) => void;
  addMagia: (nome: string) => void;
  removeMagia: (nome: string) => void;
  setCaracteristica: (key: CaracteristicaKey, valor: number) => void;
  setPvAtual: (valor: number) => void;
  setPvMax: (valor: number) => void;
  togglePvBox: (index: number, max?: number) => void;
  setPmAtual: (valor: number) => void;
  setPmMax: (valor: number) => void;
  togglePmBox: (index: number, max?: number) => void;
  setCaminhoMagia: (caminho: CaminhoMagia, focus: number) => void;
  setCampo: <K extends keyof FichaPersonagem>(
    campo: K,
    valor: FichaPersonagem[K]
  ) => void;
  setDinheiro: (valor: string) => void;
  addItem: (tipo: string, item: string) => void;
  removeItem: (tipo: string, item: string) => void;
  reset: () => void;
  /** Extrai a ficha atual para salvar na lista de personagens. */
  toFicha: () => FichaPersonagem;
  /** Carrega uma ficha salva para edição. */
  loadFromFicha: (ficha: FichaPersonagem) => void;
}

const FICHA_KEYS: (keyof FichaPersonagem)[] = [
  "nome", "nomeJogador", "nivelPontuacao", "raca", "caracteristicas",
  "pvMax", "pvAtual", "pmMax", "pmAtual", "vantagens", "desvantagens",
  "historia", "caminhosMagia", "magiasConhecidas", "dinheiro",
  "itensPorTipo", "experiencia", "tiposDano",
];

export const usePersonagemStore = create<PersonagemState>((set, get) => ({
  ...FICHA_INICIAL,

  setNivelPontuacao: (nivel) => set({ nivelPontuacao: nivel }),
  setRaca: (raca) =>
    set((s) => {
      const excluidasV = raca ? RACA_EXCLUI_VANTAGEM[raca] ?? [] : [];
      const excluidasD = raca ? RACA_EXCLUI_DESVANTAGEM[raca] ?? [] : [];
      const vantagens = excluidasV.length
        ? s.vantagens.filter((v) => !excluidasV.includes(v))
        : s.vantagens;
      const desvantagens = excluidasD.length
        ? s.desvantagens.filter((d) => !excluidasD.includes(d))
        : s.desvantagens;
      return { raca, vantagens, desvantagens };
    }),

  setCaracteristica: (key, valor) =>
    set((s) => {
      const max = MAX_CARAC_FOCUS[s.nivelPontuacao];
      return {
        caracteristicas: {
          ...s.caracteristicas,
          [key]: Math.max(0, Math.min(max, valor)),
        },
      };
    }),

  setPvAtual: (valor) =>
    set((s) => ({
      pvAtual: Math.max(0, Math.min(s.pvMax, valor)),
    })),

  setPvMax: (valor) =>
    set((s) => {
      const novoMax = Math.max(1, Math.min(30, valor));
      const pvAtual =
        novoMax > s.pvMax ? novoMax : Math.min(s.pvAtual, novoMax);
      return { pvMax: novoMax, pvAtual };
    }),

  togglePvBox: (index, max) =>
    set((s) => {
      const m = max ?? s.pvMax;
      const idx = index + 1;
      if (idx <= s.pvAtual) {
        return { pvAtual: s.pvAtual - 1 };
      }
      if (idx <= m) {
        return { pvAtual: idx };
      }
      return {};
    }),

  setPmAtual: (valor) =>
    set((s) => ({
      pmAtual: Math.max(0, Math.min(s.pmMax, valor)),
    })),

  setPmMax: (valor) =>
    set((s) => {
      const novoMax = Math.max(1, Math.min(30, valor));
      const pmAtual =
        novoMax > s.pmMax ? novoMax : Math.min(s.pmAtual, novoMax);
      return { pmMax: novoMax, pmAtual };
    }),

  togglePmBox: (index, max) =>
    set((s) => {
      const m = max ?? s.pmMax;
      const idx = index + 1;
      if (idx <= s.pmAtual) {
        return { pmAtual: s.pmAtual - 1 };
      }
      if (idx <= m) {
        return { pmAtual: idx };
      }
      return {};
    }),

  setCaminhoMagia: (caminho, focus) =>
    set((s) => {
      const max = MAX_CARAC_FOCUS[s.nivelPontuacao];
      return {
        caminhosMagia: {
          ...s.caminhosMagia,
          [caminho]: Math.max(0, Math.min(max, focus)),
        },
      };
    }),

  setCampo: (campo, valor) => set({ [campo]: valor }),

  addVantagem: (nome) =>
    set((s) => ({
      vantagens: s.vantagens.includes(nome) ? s.vantagens : [...s.vantagens, nome],
    })),
  removeVantagem: (nome) =>
    set((s) => ({ vantagens: s.vantagens.filter((x) => x !== nome) })),

  addDesvantagem: (nome) =>
    set((s) => ({
      desvantagens: s.desvantagens.includes(nome)
        ? s.desvantagens
        : [...s.desvantagens, nome],
    })),
  removeDesvantagem: (nome) =>
    set((s) => ({ desvantagens: s.desvantagens.filter((x) => x !== nome) })),

  addMagia: (nome) =>
    set((s) => ({
      magiasConhecidas: s.magiasConhecidas.includes(nome)
        ? s.magiasConhecidas
        : [...s.magiasConhecidas, nome],
    })),
  removeMagia: (nome) =>
    set((s) => ({ magiasConhecidas: s.magiasConhecidas.filter((x) => x !== nome) })),

  setDinheiro: (valor) => set({ dinheiro: valor }),

  addItem: (tipo, item) =>
    set((s) => {
      const arr = s.itensPorTipo.find((g) => g.tipo === tipo);
      if (!arr) return { itensPorTipo: [...s.itensPorTipo, { tipo, itens: [item] }] };
      if (arr.itens.includes(item)) return {};
      return {
        itensPorTipo: s.itensPorTipo.map((g) =>
          g.tipo === tipo ? { ...g, itens: [...g.itens, item] } : g
        ),
      };
    }),

  removeItem: (tipo, item) =>
    set((s) => ({
      itensPorTipo: s.itensPorTipo.map((g) =>
        g.tipo === tipo ? { ...g, itens: g.itens.filter((i) => i !== item) } : g
      ),
    })),

  reset: () => set(FICHA_INICIAL),

  toFicha: () => {
    const s = get();
    const ficha = {} as FichaPersonagem;
    for (const k of FICHA_KEYS) {
      const val = s[k as keyof typeof s];
      (ficha as unknown as Record<string, unknown>)[k] =
        typeof val === "object" && val !== null ? JSON.parse(JSON.stringify(val)) : val;
    }
    return ficha;
  },

  loadFromFicha: (ficha) =>
    set({
      nome: ficha.nome,
      nomeJogador: ficha.nomeJogador,
      nivelPontuacao: ficha.nivelPontuacao,
      raca: ficha.raca,
      caracteristicas: { ...ficha.caracteristicas },
      pvMax: ficha.pvMax,
      pvAtual: ficha.pvAtual,
      pmMax: ficha.pmMax,
      pmAtual: ficha.pmAtual,
      vantagens: [...ficha.vantagens],
      desvantagens: [...ficha.desvantagens],
      historia: ficha.historia,
      caminhosMagia: { ...ficha.caminhosMagia },
      magiasConhecidas: [...ficha.magiasConhecidas],
      dinheiro: ficha.dinheiro,
      itensPorTipo: ficha.itensPorTipo.map((g) => ({ ...g, itens: [...g.itens] })),
      experiencia: ficha.experiencia,
      tiposDano: { ...ficha.tiposDano },
    }),
}));
