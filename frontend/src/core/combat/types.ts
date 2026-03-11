export type LadoBatalha = "jogador" | "monstro";

export type TipoAcaoBasica =
  | "ataque_corpo_a_corpo"
  | "ataque_distancia"
  | "defender"
  | "esquiva"
  | "magia";

export interface EstadoLadoJogador {
  tipo: "jogador";
  nome: string;
  /** Características efetivas já com modificadores raciais aplicados */
  F: number;
  H: number;
  R: number;
  A: number;
  PdF: number;
  pvMax: number;
  pvAtual: number;
  pmMax: number;
  pmAtual: number;
  /** XP atual do personagem (para barra de progresso) */
  experiencia: number;
  /** Nomes das magias conhecidas, para menu de magias em combate */
  magiasConhecidas: string[];
  /** Tipo de dano dos ataques de Força (corte, impacto, etc.) */
  tipoDanoForca?: string;
  /** Tipo de dano dos ataques de PdF (fogo, gelo, etc.) */
  tipoDanoPdF?: string;
  /** Itens equipados ou carregados relevantes para combate */
  itensEquipados?: string[];
}

export interface EstadoLadoMonstro {
  tipo: "monstro";
  nome: string;
  F: number;
  H: number;
  R: number;
  A: number;
  PdF: number;
  pvMax: number;
  pvAtual: number;
  pmMax: number;
  pmAtual: number;
}

export type EstadoLado = EstadoLadoJogador | EstadoLadoMonstro;

export interface EstadoBatalha {
  jogador: EstadoLadoJogador;
  monstro: EstadoLadoMonstro;
  /** De quem é o turno atual */
  turnoDe: LadoBatalha;
  /** Número do round, começando em 1 */
  round: number;
  /** Já foi rodada a iniciativa deste combate */
  iniciativaResolvida: boolean;
  /** Historico simples para depuração (UI usa log narrativo separado) */
  historicoInterno: string[];
  encerrada: boolean;
  vencedor: LadoBatalha | null;
}

export interface AcaoJogador {
  lado: "jogador";
  tipo: TipoAcaoBasica;
  /** Nome da magia escolhida, quando tipo="magia" */
  magiaNome?: string;
}

export interface AcaoMonstro {
  lado: "monstro";
  tipo: TipoAcaoBasica;
  /** Nome do ataque específico do monstro, se aplicável */
  ataqueEspecifico?: string;
}

export type AcaoCombate = AcaoJogador | AcaoMonstro;

export interface ResultadoRolagem {
  d6: number;
  total: number;
}

export interface ResultadoAtaque {
  atacante: LadoBatalha;
  alvo: LadoBatalha;
  tipo: TipoAcaoBasica;
  fa: ResultadoRolagem;
  fd: ResultadoRolagem;
  acertou: boolean;
  dano: number;
  pvAlvoAntes: number;
  pvAlvoDepois: number;
  /** Descrição opcional da ação (ex.: nome da magia usada) */
  descricaoAcao?: string;
  /** Tipo de dano principal (corte, calor/fogo, etc.) quando conhecido */
  tipoDano?: string;
}

export interface MensagemMestre {
  id: string;
  autor: "mestre";
  texto: string;
  timestamp: number;
}

