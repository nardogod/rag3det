/**
 * Carregador de habilidades dos monstros do Manual (revisado).
 * Dados extraídos dos 284 monstros; descrições de vantagens_turbinado e magias_3dt.
 */

export interface HabilidadeMonstro {
  nome: string;
  descricao: string;
  fonte: string;
  monstros: string[];
  variantes: string[];
}

import habilidadesJson from "./habilidades_monstros.json";

const habilidades: HabilidadeMonstro[] = Array.isArray(habilidadesJson)
  ? (habilidadesJson as HabilidadeMonstro[])
  : [];

export function getHabilidadesMonstros(): HabilidadeMonstro[] {
  return habilidades;
}
