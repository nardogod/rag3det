/**
 * Itens do sistema 3D&T (Manual da Magia, Manual Turbinado).
 * O jogador seleciona da lista — não digita.
 */

import itensJson from "./itens_3dt.json";

export interface ItemSistema {
  nome: string;
  tipo: string;
  bonus?: string;
  custo?: string;
  efeito?: string;
  livro?: string;
  /** "Item" = item físico; "Habilidade" = habilidade de arma/armadura */
  natureza?: "Item" | "Habilidade";
}

const itens = itensJson as ItemSistema[];

/** Todos os itens do sistema */
export const itensSistema = itens;

/** Itens por tipo (Armas, Armaduras, etc.) */
export function getItensPorTipo(tipo: string): ItemSistema[] {
  return itens.filter((i) => i.tipo === tipo);
}

/** Tipos de itens disponíveis no sistema */
export const TIPOS_ITENS = [
  "Armas",
  "Armaduras",
  "Equipamento",
  "Poções",
  "Itens mágicos",
  "Outros",
] as const;
