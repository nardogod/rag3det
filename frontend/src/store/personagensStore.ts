/**
 * Lista de personagens salvos — persistida em localStorage.
 * Estrutura preparada para multi-jogador: userId opcional (null = dev local).
 * No futuro, cada jogador terá sua conta e personagens vinculados.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { FichaPersonagem } from "@/types/personagem";

const STORAGE_KEY = "3dt-personagens";

export interface PersonagemSalvo {
  id: string;
  createdAt: string;
  updatedAt: string;
  /** Futuro: id do jogador. null = dev local sem login. */
  userId?: string | null;
  ficha: FichaPersonagem;
}

function gerarId(): string {
  return crypto.randomUUID?.() ?? `p-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

interface PersonagensState {
  personagens: PersonagemSalvo[];
  personagemAtivoId: string | null;
  addPersonagem: (ficha: FichaPersonagem) => PersonagemSalvo;
  updatePersonagem: (id: string, ficha: FichaPersonagem) => void;
  removePersonagem: (id: string) => void;
  setPersonagemAtivo: (id: string | null) => void;
  getPersonagemById: (id: string) => PersonagemSalvo | null;
  getPersonagemAtivo: () => PersonagemSalvo | null;
}

export const usePersonagensStore = create<PersonagensState>()(
  persist(
    (set, get) => ({
      personagens: [],
      personagemAtivoId: null,

      addPersonagem: (ficha) => {
        const now = new Date().toISOString();
        const novo: PersonagemSalvo = {
          id: gerarId(),
          createdAt: now,
          updatedAt: now,
          userId: null,
          ficha: { ...ficha },
        };
        set((s) => ({
          personagens: [...s.personagens, novo],
          personagemAtivoId: novo.id,
        }));
        return novo;
      },

      updatePersonagem: (id, ficha) => {
        const now = new Date().toISOString();
        set((s) => ({
          personagens: s.personagens.map((p) =>
            p.id === id ? { ...p, ficha: { ...ficha }, updatedAt: now } : p
          ),
        }));
      },

      removePersonagem: (id) => {
        set((s) => ({
          personagens: s.personagens.filter((p) => p.id !== id),
          personagemAtivoId: s.personagemAtivoId === id ? null : s.personagemAtivoId,
        }));
      },

      setPersonagemAtivo: (id) => set({ personagemAtivoId: id }),

      getPersonagemById: (id) =>
        get().personagens.find((p) => p.id === id) ?? null,

      getPersonagemAtivo: () => {
        const id = get().personagemAtivoId;
        return id ? get().getPersonagemById(id) ?? null : null;
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (s) => ({
        personagens: s.personagens,
        personagemAtivoId: s.personagemAtivoId,
      }),
    }
  )
);
