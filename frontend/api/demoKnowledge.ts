export interface KnowledgeEntry {
  title: string;
  kind: "magia" | "vantagem" | "desvantagem" | "raca" | "item" | "monstro";
  source: string;
  content: string;
}

export const demoKnowledgeBase: KnowledgeEntry[] = [
  {
    title: "Área de Batalha",
    kind: "vantagem",
    source: "Manual 3D&T Turbinado",
    content:
      "Vantagem que permite levar o combate para um campo especial favorável ao personagem. Em geral é usada para controlar o terreno e ganhar vantagem tática na luta.",
  },
  {
    title: "Aceleração",
    kind: "vantagem",
    source: "Manual 3D&T Turbinado",
    content:
      "Vantagem que melhora perseguição e combate. Pode conceder bônus em iniciativa e permitir ação extra mediante gasto de PM, dependendo da situação.",
  },
  {
    title: "Adaptador",
    kind: "vantagem",
    source: "Manual 3D&T Turbinado",
    content:
      "Vantagem que permite mudar o tipo de dano dos ataques do personagem, como corte, impacto ou perfuração.",
  },
  {
    title: "Aliado",
    kind: "vantagem",
    source: "Manual 3D&T Turbinado",
    content:
      "Vantagem que representa um companheiro NPC ao lado do personagem. O custo varia conforme o poder e a utilidade desse aliado.",
  },
  {
    title: "Aparência Inofensiva",
    kind: "vantagem",
    source: "Manual 3D&T Turbinado",
    content:
      "Vantagem voltada a enganar oponentes. Pode ajudar em surpresa e em perícias sociais ligadas a parecer inofensivo ou pouco ameaçador.",
  },
  {
    title: "Dragão do Ar Adulto",
    kind: "monstro",
    source: "Manual dos Monstros",
    content:
      "Monstro de escala elevada ligado ao elemento ar. Costuma ter grande mobilidade, comportamento menos agressivo que outros dragões e capacidades ligadas a vento, deslocamento e controle do campo de batalha.",
  },
  {
    title: "Harpia",
    kind: "monstro",
    source: "Manual dos Monstros",
    content:
      "Criatura alada com comportamento oportunista, normalmente associada a ataques rápidos, emboscadas e vantagem de mobilidade aérea.",
  },
  {
    title: "Katana",
    kind: "item",
    source: "Itens 3D&T",
    content:
      "Arma cortante tradicional. Em fichas de personagem e combate costuma aparecer como equipamento ofensivo principal.",
  },
  {
    title: "Armadura de Couro",
    kind: "item",
    source: "Itens 3D&T",
    content:
      "Armadura leve usada para melhorar defesa sem o peso de armaduras pesadas. Boa opção para personagens que precisam de mobilidade.",
  },
  {
    title: "Raça",
    kind: "raca",
    source: "Manual 3D&T Turbinado",
    content:
      "No projeto, raças são tratadas como Vantagens Únicas. Cada personagem pode ter apenas uma e ela pode conceder pacote racial com vantagens, desvantagens e modificadores automáticos.",
  },
];
