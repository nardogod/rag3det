/**
 * Tipos de dano para ataques (Força e Poder de Fogo).
 * Base: Manual 3D&T Turbinado — Adaptador, Armadura Extra, Vulnerabilidade.
 * Nenhum campo livre: usuário escolhe entre opções.
 */

/** Tipos de dano para ataques corpo-a-corpo (Força) */
export const TIPOS_DANO_FORCA = [
  "",
  "corte",
  "impacto",
  "perfuração",
  "contusão",
  "agarramento",
] as const;

/** Tipos de dano para ataques à distância (Poder de Fogo) */
export const TIPOS_DANO_PDF = [
  "",
  "corte",
  "impacto",
  "perfuração",
  "calor/fogo",
  "frio",
  "eletricidade",
  "ácido",
  "luz",
  "trevas",
  "energia",
  "som",
] as const;

export type TipoDanoForca = (typeof TIPOS_DANO_FORCA)[number];
export type TipoDanoPdF = (typeof TIPOS_DANO_PDF)[number];
