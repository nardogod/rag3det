import type { Monstro } from "@/types/monstro";
import { calcularForcaMonstro } from "./forcaMonstro";

export interface LootItem {
  descricao: string;
}

export function sortearLoot(monstro: Monstro): LootItem[] {
  const resultados: LootItem[] = [];
  const forca = calcularForcaMonstro(monstro);

  const roll = () => Math.random();

  const chanceMoedas = Math.min(0.9, 0.3 + forca / 200);
  if (roll() < chanceMoedas) {
    const qtdBase = 1 + Math.floor(forca / 10);
    const qtd = qtdBase + Math.floor(Math.random() * (1 + qtdBase));
    resultados.push({
      descricao: `${qtd} moedas`,
    });
  }

  const tesouroTexto = (monstro.tesouro || "").trim();
  if (tesouroTexto) {
    const chanceTesouroRaro = 0.25;
    if (roll() < chanceTesouroRaro) {
      resultados.push({
        descricao: tesouroTexto,
      });
    }
  }

  return resultados;
}

