/**
 * Lógica de construção de personagem 3D&T.
 * Base: Manual 3D&T Turbinado, pontuação e dependências.
 */

import type {
  Caracteristicas,
  CaminhosMagia,
  NivelPontuacao,
} from "@/types/personagem";

export const PONTUACAO_BASE: Record<NivelPontuacao, number> = {
  pessoa_comum: 4,
  novato: 5,
  lutador: 7,
  campeao: 10,
  lenda: 12,
};

export const MAX_CARAC_FOCUS: Record<NivelPontuacao, number> = {
  pessoa_comum: 1,
  novato: 3,
  lutador: 4,
  campeao: 5,
  lenda: 5,
};

/** Custo em pontos das características (1 pt = 1 carac) */
export function custoCaracteristicas(c: Caracteristicas): number {
  return (c.F || 0) + (c.H || 0) + (c.R || 0) + (c.A || 0) + (c.PdF || 0);
}

/** Custo em pontos dos caminhos da magia (Focus = 1 pt cada) */
export function custoCaminhosMagia(cm: CaminhosMagia): number {
  return (
    (cm.Água || 0) + (cm.Ar || 0) + (cm.Fogo || 0) +
    (cm.Luz || 0) + (cm.Terra || 0) + (cm.Trevas || 0)
  );
}

/** Pontos gastos em vantagens (soma dos custos) */
export function custoVantagens(
  nomes: string[],
  getCusto: (nome: string) => number
): number {
  return nomes.reduce((acc, n) => acc + getCusto(n), 0);
}

/** Pontos ganhos com desvantagens (valor negativo = ganho) */
export function pontosDesvantagens(
  nomes: string[],
  getCusto: (nome: string) => number
): number {
  return nomes.reduce((acc, n) => {
    const c = getCusto(n);
    return acc + (c < 0 ? Math.abs(c) : 0);
  }, 0);
}

/** Custo da raça (única). Valores negativos = desvantagem racial (ex.: Morto-Vivo -2, Goblin -2) dão pontos extras. */
export function custoRaca(nome: string | null, getCusto: (nome: string) => number): number {
  if (!nome) return 0;
  return getCusto(nome);
}

/** Custo em pontos das magias conhecidas (1 pt cada). */
export function custoMagiasConhecidas(magias: string[]): number {
  return magias.length;
}

/**
 * Calcula pontos disponíveis.
 * total = base + desvantagens - carac - caminhos - vantagens - raça - magias
 */
export function pontosDisponiveis(
  nivel: NivelPontuacao,
  caracteristicas: Caracteristicas,
  caminhosMagia: CaminhosMagia,
  vantagens: string[],
  desvantagens: string[],
  raca: string | null,
  magiasConhecidas: string[],
  getCustoVantagem: (nome: string) => number,
  getCustoDesvantagem: (nome: string) => number,
  getCustoRaca: (nome: string) => number
): number {
  const base = PONTUACAO_BASE[nivel];
  const desv = pontosDesvantagens(desvantagens, getCustoDesvantagem);
  const total = base + desv;
  const gasto =
    custoCaracteristicas(caracteristicas) +
    custoCaminhosMagia(caminhosMagia) +
    custoVantagens(vantagens, getCustoVantagem) +
    custoRaca(raca, getCustoRaca) +
    custoMagiasConhecidas(magiasConhecidas);
  return total - gasto;
}

/**
 * PV base = R × 5 (mín. 1). Manual 3D&T: "PVs=Rx5" (ex.: Koi R3 → 15 PVs).
 * +5 por cada vantagem "Pontos de Vida Extras".
 */
export function calcularPvMax(
  rEfetivo: number,
  vantagens: string[]
): number {
  const base = Math.max(1, 5 * rEfetivo);
  const extras = vantagens.filter((n) => n === "Pontos de Vida Extras").length;
  return base + extras * 5;
}

/**
 * PM base = R × 5 (mín. 1). Manual 3D&T: mesma quantidade que PVs.
 * +5 por cada vantagem "Pontos de Magia Extras".
 */
export function calcularPmMax(
  rEfetivo: number,
  vantagens: string[]
): number {
  const base = Math.max(1, 5 * rEfetivo);
  const extras = vantagens.filter((n) => n === "Pontos de Magia Extras").length;
  return base + extras * 5;
}

/** Valida se personagem está dentro dos limites do nível */
export function validarLimites(
  nivel: NivelPontuacao,
  caracteristicas: Caracteristicas,
  caminhosMagia: CaminhosMagia
): { valido: boolean; erros: string[] } {
  const max = MAX_CARAC_FOCUS[nivel];
  const erros: string[] = [];
  const caracs = [caracteristicas.F, caracteristicas.H, caracteristicas.R, caracteristicas.A, caracteristicas.PdF];
  caracs.forEach((v, i) => {
    if ((v || 0) > max) erros.push(`Característica ${["F","H","R","A","PdF"][i]} não pode exceder ${max}`);
  });
  const paths = Object.values(caminhosMagia);
  paths.forEach((v) => {
    if ((v || 0) > max) erros.push(`Focus não pode exceder ${max}`);
  });
  return { valido: erros.length === 0, erros };
}
