/**
 * Estado global do bestiário (Zustand).
 */

import { create } from "zustand";
import type { Monstro } from "@/types/monstro";
import type { OrdemBestiario } from "@/core/bestiario";

interface BestiarioState {
  livroSelecionado: string | null;
  filtroTipo: string | null;
  ordem: OrdemBestiario;
  monstroSelecionado: Monstro | null;
  setLivroSelecionado: (livro: string | null) => void;
  setFiltroTipo: (tipo: string | null) => void;
  setOrdem: (ordem: OrdemBestiario) => void;
  setMonstroSelecionado: (monstro: Monstro | null) => void;
}

export const useBestiarioStore = create<BestiarioState>((set) => ({
  livroSelecionado: null,
  filtroTipo: null,
  ordem: "alfabetica",
  monstroSelecionado: null,
  setLivroSelecionado: (livro) => set({ livroSelecionado: livro }),
  setFiltroTipo: (tipo) => set({ filtroTipo: tipo }),
  setOrdem: (ordem) => set({ ordem }),
  setMonstroSelecionado: (monstro) => set({ monstroSelecionado: monstro }),
}));
