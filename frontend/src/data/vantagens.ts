/**
 * Dados de Vantagens, Desvantagens e Raças (Únicas).
 * Fonte: vantagens_turbinado.json
 *
 * ESPECIFICAÇÃO ÚNICAS:
 * - Vantagens Únicas (tipo "unica" ou unica: true) = raças. Cada personagem pode ter apenas uma.
 * - Desvantagens Únicas (unica: true) = apenas uma por personagem.
 * - Vantagens/Desvantagens comuns = unica: false.
 */

import vantagensJson from "./vantagens_turbinado.json";

export interface ItemVantagem {
  nome: string;
  tipo: "vantagem" | "desvantagem" | "unica";
  /** true = Única (apenas uma por personagem). Raças são sempre únicas. */
  unica?: boolean;
  custo: string;
  efeito: string;
  livro?: string;
  pagina?: number;
}

const raw = vantagensJson as ItemVantagem[];

/** Indica se o item é Único (apenas um por personagem). */
export function isUnica(item: ItemVantagem): boolean {
  return item.tipo === "unica" || item.unica === true;
}

/** Extrai custo numérico do texto (ex.: "2 pontos" -> 2, "-1 ponto" -> -1) */
export function parseCusto(custo: string): number {
  if (!custo) return 0;
  const lower = custo.toLowerCase();
  if (lower.includes("variável") || lower.includes("variavel")) return 0;
  if (lower.includes("especial")) return 0;
  if (lower.includes("negativo")) return -1; // desvantagem genérica
  const match = custo.match(/(-?\d+)\s*(ponto|pts?)/i);
  if (match) return parseInt(match[1], 10);
  const num = custo.match(/(-?\d+)/);
  return num ? parseInt(num[1], 10) : 0;
}

export const vantagens = raw.filter((x) => x.tipo === "vantagem");
export const desvantagens = raw.filter((x) => x.tipo === "desvantagem");
/** Raças = Vantagens Únicas (cada personagem pode ter apenas uma). */
export const racas = raw.filter((x) => x.tipo === "unica" || x.unica === true);
/** Desvantagens Únicas (apenas uma por personagem). */
export const desvantagensUnicas = desvantagens.filter((x) => x.unica === true);

export function getVantagem(nome: string): ItemVantagem | undefined {
  return raw.find((x) => x.nome === nome);
}

export function getDesvantagem(nome: string): ItemVantagem | undefined {
  return raw.find((x) => x.tipo === "desvantagem" && x.nome === nome);
}

export function getRaca(nome: string): ItemVantagem | undefined {
  return racas.find((x) => x.nome === nome);
}
