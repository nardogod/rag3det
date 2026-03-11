/** Características 3D&T: F, H, R, A, PdF */
export interface Caracteristicas {
  F?: string;
  H?: string;
  R?: string;
  A?: string;
  PdF?: string;
}

/** Ataque específico com nome, FA/FD e dano */
export interface AtaqueEspecifico {
  nome?: string;
  fa_fd?: string;
  dano?: string;
}

export type TipoMonstro =
  | "humanóide"
  | "besta"
  | "elemental"
  | "morto-vivo"
  | "construto"
  | "espírito"
  | "outro";

/** Monstro do modelo enriquecido (formato completo da ficha) */
export interface Monstro {
  nome: string;
  tipo?: TipoMonstro | string;
  caracteristicas?: Caracteristicas;
  pv?: string;
  pm?: string;
  habilidades?: string[];
  vulnerabilidades?: string[];
  fraqueza?: string;
  descricao?: string;
  livro?: string;
  pagina?: number;
  habilidades_combate?: string[];
  comportamento?: string;
  altura_tamanho?: string | null;
  peso?: string | null;
  habitat?: string | null;
  comportamento_dia_noite?: string | null;
  comportamento_combate?: string | null;
  habilidades_extra?: string | null;
  movimento?: string | null;
  ataques_especificos?: AtaqueEspecifico[] | null;
  imunidades?: string[] | null;
  fraquezas?: string[] | null;
  origem_criacao?: string | null;
  uso_cultural?: string | null;
  vinculo_montaria?: string | null;
  veneno_detalhado?: string | null;
  resistencia_controle?: string | null;
  necessidades?: string | null;
  recuperacao_pv?: string | null;
  taticas?: string | null;
  tesouro?: string | null;
  escala?: string | null;
  fonte_referencia?: string | null;
}

/** Linha da ficha formatada (campo, valor) */
export interface LinhaFicha {
  campo: string;
  valor: string;
}
