/**
 * Pacote racial: vantagens, desvantagens e modificadores automáticos por raça.
 * Ao escolher uma raça, estes itens são aplicados automaticamente (incluídos no custo da raça).
 * Base: Manual 3D&T Turbinado, Manual da Magia, Manual dos Monstros.
 */

import type { Caracteristicas } from "@/types/personagem";

export interface PacoteRacial {
  /** Vantagens que a raça concede automaticamente (não custam pontos extras) */
  vantagens: string[];
  /** Desvantagens que a raça impõe automaticamente (não dão pontos extras) */
  desvantagens: string[];
  /** Modificadores às características (ex.: Anão +1 R) */
  modificadores: Partial<Caracteristicas>;
  /** Efeitos especiais em texto (regras que não mapeiam a vantagens/desvantagens) */
  efeitosEspeciais?: string[];
}

/** Pacotes raciais por nome da raça */
export const RACA_PACOTE: Record<string, PacoteRacial> = {
  Anão: {
    vantagens: ["Infravisão", "Resistência à Magia"],
    desvantagens: [],
    modificadores: { R: 1 },
    efeitosEspeciais: ["Apenas em fantasia medieval"],
  },
  Anfíbio: {
    vantagens: ["Respira na água", "Radar", "Ambiente Especial (água)"],
    desvantagens: [],
    modificadores: {},
    efeitosEspeciais: ["Sentidos Especiais (Radar) apenas na água"],
  },
  Centauro: {
    vantagens: ["Modelo Especial", "2 ataques com patas"],
    desvantagens: [],
    modificadores: {},
  },
  Construto: {
    vantagens: ["Imune a veneno", "Imune a efeitos mentais"],
    desvantagens: ["Recuperação Limitada"],
    modificadores: {},
    efeitosEspeciais: ["Não recupera PV por descanso", "Não combina com fantasia medieval ou torneios"],
  },
  Elfo: {
    vantagens: [],
    desvantagens: [],
    modificadores: {},
    efeitosEspeciais: ["Pacote variável — ver Manual p. 41"],
  },
  Fada: {
    vantagens: ["Aparência Inofensiva", "Arcano", "Levitação", "Modelo Especial"],
    desvantagens: ["Vulnerabilidade"],
    modificadores: { H: 1 },
    efeitosEspeciais: ["H+1 até máx H5", "Vulnerabilidade: magia e armas mágicas"],
  },
  Goblin: {
    vantagens: [],
    desvantagens: [],
    modificadores: {},
    efeitosEspeciais: ["Pacote variável — ver Manual p. 41"],
  },
  Halfling: {
    vantagens: [],
    desvantagens: [],
    modificadores: {},
    efeitosEspeciais: ["Pacote variável — ver Manual p. 41"],
  },
  "Meio-Dragão": {
    vantagens: [],
    desvantagens: [],
    modificadores: {},
    efeitosEspeciais: ["Pacote variável — ver Manual p. 41"],
  },
  "Morto-Vivo": {
    vantagens: [],
    desvantagens: [],
    modificadores: {},
    efeitosEspeciais: ["Imune veneno/doenças/magia mental", "Não cura com medicina", "Devoção ou Dependência obrigatória", "Tipos: Esqueleto, Zumbi, Múmia, Fantasma, Vampiro, Lich"],
  },
  "Meio-Elfo": {
    vantagens: ["Infravisão"],
    desvantagens: [],
    modificadores: {},
    efeitosEspeciais: ["Vive 2x mais que humanos", "Pode ser Paladino"],
  },
  "Meio-Orc": {
    vantagens: ["Infravisão"],
    desvantagens: ["Má Fama"],
    modificadores: { F: 1 },
    efeitosEspeciais: ["Nunca Genialidade ou Memória Expandida", "Filhos de humanos podem ser Paladinos"],
  },
  Gnomo: {
    vantagens: ["Infravisão", "Genialidade"],
    desvantagens: [],
    modificadores: { H: 1 },
    efeitosEspeciais: ["Focus+1 em Luz", "Magias ilusórias e Invisibilidade -1 PM", "Modelo Especial", "Não nativo em Arton"],
  },
  Paladino: {
    vantagens: [],
    desvantagens: [],
    modificadores: { R: 1 },
    efeitosEspeciais: ["2 pts Focus apenas em Água, Ar e Luz", "Códigos de Honra (Heróis, Honestidade)", "Apenas humanos, Anões, Meio-Elfos e Meio-Orcs"],
  },
  Brownie: {
    vantagens: ["Modelo Especial", "Magias naturais (Proteção Mágica, Luz, Ilusão Avançada, Imagem Turva 1x/dia)"],
    desvantagens: ["Incapaz de lutar"],
    modificadores: {},
    efeitosEspeciais: ["Nunca Resistência à Magia"],
  },
  "Meio-Gênio": {
    vantagens: ["Marca de Wynna", "Pequenos Desejos", "Levitação (1 pt)", "Armadura Extra", "Feiticeiro (0 pts)"],
    desvantagens: [],
    modificadores: {},
  },
  Sátiro: {
    vantagens: ["Aparência Inofensiva", "Arcano", "Levitação", "Modelo Especial"],
    desvantagens: ["Vulnerabilidade"],
    modificadores: { H: 1 },
    efeitosEspeciais: ["Características de fada", "Vulnerabilidade: magia e armas mágicas"],
  },
  Dragonete: {
    vantagens: ["Aparência Inofensiva", "Arcano", "Levitação", "Modelo Especial", "PdF como sopro"],
    desvantagens: [],
    modificadores: { H: 1 },
    efeitosEspeciais: ["Nunca Resistência à Magia", "Sopro: fogo, água, luz ou ar"],
  },
  Grig: {
    vantagens: ["Aparência Inofensiva", "Arcano", "Levitação", "Modelo Especial"],
    desvantagens: ["Vulnerabilidade"],
    modificadores: { H: 1 },
    efeitosEspeciais: ["Nunca Resistência à Magia ou Monstruoso", "Vulnerabilidade: magia e armas mágicas"],
  },
  Pixie: {
    vantagens: ["Aparência Inofensiva", "Arcano", "Levitação", "Modelo Especial"],
    desvantagens: ["Vulnerabilidade"],
    modificadores: { H: 1 },
    efeitosEspeciais: ["Nunca Resistência à Magia", "Vulnerabilidade: magia e armas mágicas"],
  },
  Licantropo: {
    vantagens: [],
    desvantagens: ["Monstruoso", "Vulnerabilidade"],
    modificadores: { F: 1, A: 1 },
    efeitosEspeciais: ["Forma de fera: F+1, A+1", "Vulnerabilidade: magia e prata", "Transformação involuntária (Fúria, Lua Cheia, Perto da Morte)"],
  },
};

/** Retorna o pacote racial ou vazio se raça não encontrada */
export function getPacoteRacial(raca: string | null): PacoteRacial {
  if (!raca) return { vantagens: [], desvantagens: [], modificadores: {} };
  return RACA_PACOTE[raca] ?? { vantagens: [], desvantagens: [], modificadores: {} };
}

/** Aplica modificadores raciais às características base */
export function aplicarModificadoresRaca(
  base: Caracteristicas,
  raca: string | null
): Caracteristicas {
  const pacote = getPacoteRacial(raca);
  const mod = pacote.modificadores;
  if (!mod || Object.keys(mod).length === 0) return { ...base };

  return {
    F: Math.max(0, (base.F || 0) + (mod.F || 0)),
    H: Math.max(0, (base.H || 0) + (mod.H || 0)),
    R: Math.max(0, (base.R || 0) + (mod.R || 0)),
    A: Math.max(0, (base.A || 0) + (mod.A || 0)),
    PdF: Math.max(0, (base.PdF || 0) + (mod.PdF || 0)),
  };
}
