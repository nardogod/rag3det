/**
 * Dados de Magias 3D&T.
 * Fonte: magias_3dt_completo.json
 */

import magiasJson from "./magias_3dt.json";

export interface Magia {
  nome: string;
  escola?: string;
  custo?: string;
  alcance?: string;
  duracao?: string;
  descricao?: string;
  pagina?: number;
  texto_completo?: string;
  fonte?: string;
  confianca?: number;
}

const magias = magiasJson as Magia[];

/** Sanitiza escola: "NÃO ENCONTRADO" vira "—" para exibição */
function sanitizarEscola(escola: string | undefined): string | undefined {
  if (!escola) return undefined;
  if (escola.toUpperCase() === "NÃO ENCONTRADO") return "—";
  return escola;
}

export function getMagias(): Magia[] {
  return magias
    .filter((m) => m.descricao && m.descricao.length > 10)
    .map((m) => ({
      ...m,
      escola: sanitizarEscola(m.escola) ?? m.escola,
    }));
}

export function getMagia(nome: string): Magia | undefined {
  return magias.find((m) => m.nome === nome);
}

export function searchMagias(query: string): Magia[] {
  const q = query.toLowerCase().trim();
  if (!q) return magias.slice(0, 50);
  return magias.filter((m) => m.nome.toLowerCase().includes(q)).slice(0, 50);
}
