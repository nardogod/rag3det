/**
 * Dependências entre escolhas no 3D&T.
 * Ao escolher X, ficam disponíveis B e C e ficam excluídos H, G, F.
 * Base: Manual 3D&T Turbinado, Manual da Magia.
 * Regras em cascata: escolhas respeitam o livro e escolhas anteriores.
 */

import type { CaminhosMagia, NivelPontuacao } from "@/types/personagem";

/** Mapeia escola de magia para Caminho (Focus) */
const ESCOLA_PARA_CAMINHO: Record<string, string[]> = {
  "elemental (água)": ["Água"],
  "elemental (ar)": ["Ar"],
  "elemental (fogo)": ["Fogo"],
  "elemental (terra)": ["Terra"],
  "elemental (todas)": ["Água", "Ar", "Fogo", "Terra"],
  branca: ["Luz"],
  negra: ["Trevas"],
  trevas: ["Trevas"],
  luz: ["Luz"],
  água: ["Água"],
  ar: ["Ar"],
  fogo: ["Fogo"],
  terra: ["Terra"],
  espírito: ["Luz", "Trevas"],
};

function escolasDaMagia(escola: string | undefined): string[] {
  if (!escola) return [];
  const partes = escola.toLowerCase().split(/[,;]/).map((s) => s.trim());
  const caminhos: string[] = [];
  for (const p of partes) {
    const arr = ESCOLA_PARA_CAMINHO[p];
    if (arr) {
      caminhos.push(...arr);
    } else {
      const m = p.match(/elemental\s*\((\w+)\)/);
      if (m) {
        const elem = m[1].toLowerCase();
        const key = `elemental (${elem})`;
        const arr2 = ESCOLA_PARA_CAMINHO[key];
        if (arr2) caminhos.push(...arr2);
        else caminhos.push(elem.charAt(0).toUpperCase() + elem.slice(1));
      } else {
        const arr3 = ESCOLA_PARA_CAMINHO[p];
        if (arr3) caminhos.push(...arr3);
      }
    }
  }
  return [...new Set(caminhos)];
}

/** Verifica se personagem tem Focus suficiente para a magia */
export function podeAprenderMagia(
  escola: string | undefined,
  caminhosMagia: CaminhosMagia
): boolean {
  const caminhos = escolasDaMagia(escola);
  if (caminhos.length === 0) return true; // sem escola = disponível
  return caminhos.some((c) => (caminhosMagia[c as keyof CaminhosMagia] || 0) >= 1);
}

/** Vantagens excluídas por raça (Manual da Magia: "Nunca Resistência à Magia", etc.) */
export const RACA_EXCLUI_VANTAGEM: Record<string, string[]> = {
  Fada: ["Resistência à Magia"],
  Brownie: ["Resistência à Magia"],
  Grig: ["Resistência à Magia", "Monstruoso"],
  Pixie: ["Resistência à Magia"],
  Dragonete: ["Resistência à Magia"],
  Sátiro: ["Resistência à Magia"], // características de fada
};

/** Vantagens que exigem Magia ou Focus em algum caminho (Manual da Magia) */
const VANTAGEM_REQUER: Record<string, string[]> = {
  Arcano: ["Magia"],
  Clericato: ["Magia"],
  Familiares: ["Magia"], // "Apenas usuários de magia"
};

/** Desvantagens excluídas por raça (Manual da Magia) */
export const RACA_EXCLUI_DESVANTAGEM: Record<string, string[]> = {
  Construto: ["Vulnerabilidade"], // regras especiais de Construto
};

/** Vantagens que se excluem mutuamente (Manual 3D&T) */
const VANTAGENS_EXCLUEM: [string, string][] = [];

/** Desvantagens que se excluem mutuamente (Manual da Magia p. 106) */
const DESVANTAGENS_EXCLUEM: [string, string][] = [
  ["Código de Honestidade", "Mentiroso Compulsivo"],
];

/** Máximo de vantagens escolhidas pelo jogador por nível (Manual p. 9). Raça não conta. */
const MAX_VANTAGENS_ESCOLHIDAS: Record<NivelPontuacao, number> = {
  pessoa_comum: 2,
  novato: 2,
  lutador: 999,
  campeao: 999,
  lenda: 999,
};

/** Regras de desvantagens por nível: até N de custo X ou M de custo Y (Manual p. 9) */
function limitesDesvantagens(nivel: NivelPontuacao): {
  maxDesvCusto1: number;
  maxDesvCusto2: number;
  maxDesvQualquer: number;
} {
  switch (nivel) {
    case "pessoa_comum":
      return { maxDesvCusto1: 1, maxDesvCusto2: 0, maxDesvQualquer: 0 };
    case "novato":
      return { maxDesvCusto1: 3, maxDesvCusto2: 1, maxDesvQualquer: 0 };
    case "lutador":
      return { maxDesvCusto1: 3, maxDesvCusto2: 2, maxDesvQualquer: 1 };
    case "campeao":
      return { maxDesvCusto1: 3, maxDesvCusto2: 3, maxDesvQualquer: 2 };
    case "lenda":
      return { maxDesvCusto1: 3, maxDesvCusto2: 3, maxDesvQualquer: 3 };
  }
}

export interface EstadoPersonagem {
  raca: string | null;
  /** Vantagens escolhidas + vantagens raciais (para filtros de dependência) */
  vantagens: string[];
  desvantagens: string[];
  caminhosMagia: CaminhosMagia;
  /** Nível de pontuação (para limites por nível) */
  nivel?: NivelPontuacao;
  /** Vantagens escolhidas pelo jogador (sem raciais) — para limite de quantidade */
  vantagensEscolhidas?: string[];
  /** Desvantagens escolhidas pelo jogador (sem raciais) — para limite por nível */
  desvantagensEscolhidas?: string[];
  /** Função para obter custo de desvantagem (para limites por custo) */
  getCustoDesvantagem?: (nome: string) => number;
}

/** Tem Focus em algum caminho? */
function temFocusMagia(caminhosMagia: CaminhosMagia): boolean {
  return Object.values(caminhosMagia).some((v) => (v || 0) >= 1);
}

/** Verifica se pode adicionar mais uma vantagem (limite por nível) */
function podeAdicionarVantagem(estado: EstadoPersonagem): boolean {
  const nivel = estado.nivel ?? "novato";
  const escolhidas = estado.vantagensEscolhidas ?? estado.vantagens;
  const max = MAX_VANTAGENS_ESCOLHIDAS[nivel];
  return escolhidas.length < max;
}

/** Filtra vantagens disponíveis dado o estado (regras em cascata) */
export function vantagensDisponiveis(
  todas: { nome: string }[],
  estado: EstadoPersonagem
): { nome: string }[] {
  const excluidasPorRaca = estado.raca
    ? RACA_EXCLUI_VANTAGEM[estado.raca] ?? []
    : [];
  const limiteVantagens = !podeAdicionarVantagem(estado);
  return todas.filter((v) => {
    if (excluidasPorRaca.includes(v.nome)) return false;
    if (limiteVantagens) return false; // já atingiu o máximo do nível
    const requer = VANTAGEM_REQUER[v.nome];
    if (requer?.length) {
      const temRequisito =
        requer.some((r) => estado.vantagens.includes(r)) ||
        temFocusMagia(estado.caminhosMagia);
      if (!temRequisito) return false;
    }
    const excluiCom = VANTAGENS_EXCLUEM.find(([a, b]) => a === v.nome || b === v.nome);
    if (excluiCom) {
      const outra = excluiCom[0] === v.nome ? excluiCom[1] : excluiCom[0];
      if (estado.vantagens.includes(outra)) return false;
    }
    return true;
  });
}

/** Custo absoluto da desvantagem (1 a 4). 0 se não conseguir parsear. */
function custoAbsDesvantagem(custo: number): number {
  const abs = Math.abs(custo);
  return abs >= 1 && abs <= 4 ? abs : 1;
}

/** Verifica se pode adicionar desvantagem com dado custo (regras Manual p. 9) */
function podeAdicionarDesvantagem(
  nivel: NivelPontuacao,
  desvantagensAtuais: string[],
  custoNova: number,
  getCusto: (nome: string) => number
): boolean {
  const custoAbs = custoAbsDesvantagem(custoNova);
  const limites = limitesDesvantagens(nivel);
  const n1 = desvantagensAtuais.filter((n) => Math.abs(getCusto(n)) === 1).length;
  const n2 = desvantagensAtuais.filter((n) => Math.abs(getCusto(n)) === 2).length;
  const nQualquer = desvantagensAtuais.filter((n) => {
    const c = Math.abs(getCusto(n));
    return c === 3 || c === 4;
  }).length;

  switch (nivel) {
    case "pessoa_comum":
      return n1 < 1 && custoAbs === 1;
    case "novato":
      if (custoAbs === 1) return n2 === 0 && nQualquer === 0 && n1 < limites.maxDesvCusto1;
      if (custoAbs === 2) return n1 === 0 && nQualquer === 0 && n2 < limites.maxDesvCusto2;
      return false;
    case "lutador":
      if (custoAbs === 1) return n2 === 0 && nQualquer === 0 && n1 < limites.maxDesvCusto1;
      if (custoAbs === 2) return n1 === 0 && nQualquer === 0 && n2 < limites.maxDesvCusto2;
      if (custoAbs >= 3) return n1 === 0 && n2 === 0 && nQualquer < limites.maxDesvQualquer;
      return false;
    case "campeao":
      if (custoAbs <= 2) return nQualquer === 0 && n1 + n2 < 3;
      return n1 === 0 && n2 === 0 && nQualquer < limites.maxDesvQualquer;
    case "lenda":
      return n1 + n2 + nQualquer < 3;
  }
  return false;
}

/** Filtra desvantagens disponíveis (regras em cascata) */
export function desvantagensDisponiveis(
  todas: { nome: string }[],
  estado: EstadoPersonagem
): { nome: string }[] {
  const excluidasPorRaca = estado.raca
    ? RACA_EXCLUI_DESVANTAGEM[estado.raca] ?? []
    : [];
  const getCusto = estado.getCustoDesvantagem ?? (() => 1);
  const nivel = estado.nivel ?? "novato";
  const desvEscolhidas = estado.desvantagensEscolhidas ?? estado.desvantagens;

  return todas.filter((d) => {
    if (excluidasPorRaca.includes(d.nome)) return false;
    const excluiCom = DESVANTAGENS_EXCLUEM.find(([a, b]) => a === d.nome || b === d.nome);
    if (excluiCom) {
      const outra = excluiCom[0] === d.nome ? excluiCom[1] : excluiCom[0];
      if (desvEscolhidas.includes(outra)) return false;
    }
    const custo = getCusto(d.nome);
    if (!podeAdicionarDesvantagem(nivel, desvEscolhidas, custo, getCusto)) return false;
    return true;
  });
}

/** Filtra magias disponíveis (exige Focus no caminho) */
export function magiasDisponiveis<T extends { nome: string; escola?: string }>(
  todas: T[],
  caminhosMagia: CaminhosMagia
): T[] {
  return todas.filter((m) => podeAprenderMagia(m.escola, caminhosMagia));
}

/** Raças: apenas uma por personagem; algumas podem ser excluídas por cenário (não implementado) */
export function racasDisponiveis<T extends { nome: string }>(
  todas: T[],
  _estado: EstadoPersonagem
): T[] {
  return todas;
}
