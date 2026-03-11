/**
 * Sanitização agressiva para exibição de monstros.
 * Garante saída legível e coerente com o sistema.
 * Pipeline: controle → normalizarOcr → limpeza agressiva → espaços
 */

import { normalizarOcr } from "./normalizarOcr";

/** Remove caracteres de controle (form feed, etc.) */
function removerCaracteresControle(texto: string): string {
  return texto.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, "");
}

/**
 * Limpeza agressiva pós-OCR: corrige artefatos restantes.
 * Padrões que não cabem no normalizarOcr ou precisam de contexto.
 */
function limpezaAgressiva(texto: string): string {
  let t = texto;

  // Números com espaço no meio: 10-1 5 → 10-15, 10-1 5 → 10-15
  t = t.replace(/(\d+)-1\s+5\b/g, "$1-15");
  t = t.replace(/(\d+)-1\s+(\d)\b/g, "$1-1$2");

  // Stats garbled
  t = t.replace(/\bII\s+TO\b/gi, "AGI");
  t = t.replace(/\bDE\s+XO\b/gi, "DEX 0");
  t = t.replace(/\bPE\s+R\b/gi, "PER");
  t = t.replace(/\bFR\s+S-/gi, "FR 5-");

  // Quote garbage: ''.)ú111 → Só
  t = t.replace(/['"]+\.\)?ú111\s*/gi, "Só ");
  t = t.replace(/['"]+\.\)?[úu]1+1*\s*/gi, "Só ");

  // Ataques com backslash/tab/garbage
  t = t.replace(/#!?[\s\\]+taques/gi, "#Ataques");
  t = t.replace(/#!?[\s\\]+aques/gi, "#Ataques");
  t = t.replace(/#\s*Ataques\s+fll/gi, "#Ataques [1]");

  // Percentual: 90°10 → 90%
  t = t.replace(/(\d+)°10\b/g, "$1%");
  t = t.replace(/(\d+)°\s*(\d+)/g, "$1%");

  // "li" isolado entre números (F3-4, li F3) → remover ou corrigir
  t = t.replace(/\bli\s+F(\d)/gi, " F$1");

  // Múltiplos espaços
  t = t.replace(/\s{2,}/g, " ");
  t = t.replace(/\s+\./g, ".");
  t = t.replace(/\s+,/g, ",");

  return t.trim();
}

/**
 * Sanitiza texto para exibição no bestiário.
 * Único ponto de saída: garante coerência em toda a UI.
 */
export function sanitizarTextoExibicao(texto: string | null | undefined): string {
  if (texto == null || typeof texto !== "string") return "";
  let t = removerCaracteresControle(texto);
  t = normalizarOcr(t);
  t = limpezaAgressiva(t);
  return t;
}
