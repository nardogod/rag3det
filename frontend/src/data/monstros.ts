/**
 * Carregador de dados de monstros.
 * Data Driven: dados estáticos em JSON.
 */

import type { Monstro } from "@/types/monstro";

// Importação direta do JSON (Vite suporta)
import monstrosJson from "./monstros.json";

const monstros: Monstro[] = Array.isArray(monstrosJson)
  ? (monstrosJson as Monstro[])
  : [];

/**
 * Retorna todos os monstros do modelo enriquecido.
 */
export function getMonstros(): Monstro[] {
  return monstros;
}
