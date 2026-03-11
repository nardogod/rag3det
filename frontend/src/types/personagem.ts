/**
 * Ficha de Personagem 3D&T — Manual 3D&T Turbinado Digital, p. 144
 */

export type CaracteristicaKey = "F" | "H" | "R" | "A" | "PdF";

export interface Caracteristicas {
  F: number;
  H: number;
  R: number;
  A: number;
  PdF: number;
}

export const CAMINHOS_MAGIA = [
  "Água",
  "Ar",
  "Fogo",
  "Luz",
  "Terra",
  "Trevas",
] as const;

export type CaminhoMagia = (typeof CAMINHOS_MAGIA)[number];

export interface CaminhosMagia {
  Água: number;
  Ar: number;
  Fogo: number;
  Luz: number;
  Terra: number;
  Trevas: number;
}

export type NivelPontuacao = "pessoa_comum" | "novato" | "lutador" | "campeao" | "lenda";

export interface FichaPersonagem {
  nome: string;
  nomeJogador: string;
  nivelPontuacao: NivelPontuacao;
  raca: string | null;
  caracteristicas: Caracteristicas;
  pvMax: number;
  pvAtual: number;
  pmMax: number;
  pmAtual: number;
  vantagens: string[];
  desvantagens: string[];
  historia: string;
  caminhosMagia: CaminhosMagia;
  magiasConhecidas: string[];
  /** Valor em moedas (ex.: "1dx100 Moedas") */
  dinheiro: string;
  /** Itens agrupados por tipo */
  itensPorTipo: { tipo: string; itens: string[] }[];
  experiencia: number;
  tiposDano: { Força: string; "Poder de Fogo": string };
}

export const FICHA_INICIAL: FichaPersonagem = {
  nome: "",
  nomeJogador: "",
  nivelPontuacao: "novato",
  raca: null,
  caracteristicas: { F: 0, H: 0, R: 0, A: 0, PdF: 0 },
  pvMax: 1,
  pvAtual: 1,
  pmMax: 1,
  pmAtual: 1,
  vantagens: [],
  desvantagens: [],
  historia: "",
  caminhosMagia: {
    Água: 0,
    Ar: 0,
    Fogo: 0,
    Luz: 0,
    Terra: 0,
    Trevas: 0,
  },
  magiasConhecidas: [],
  dinheiro: "",
  itensPorTipo: [
    { tipo: "Armas", itens: [] },
    { tipo: "Armaduras", itens: [] },
    { tipo: "Equipamento", itens: [] },
    { tipo: "Poções", itens: [] },
    { tipo: "Itens mágicos", itens: [] },
    { tipo: "Outros", itens: [] },
  ],
  experiencia: 0,
  tiposDano: { Força: "", "Poder de Fogo": "" },
};
