import { getMagia } from "@/data/magias";

export function obterCustoPmMagia(nome: string): number {
  const magia = getMagia(nome);
  if (!magia?.custo) {
    return 1;
  }
  const match = magia.custo.match(/(\d+)/);
  const valor = match ? parseInt(match[1], 10) : Number.NaN;
  if (Number.isNaN(valor) || valor <= 0) {
    return 1;
  }
  return valor;
}

export function estimarPotenciaMagia(nome: string): number {
  const magia = getMagia(nome);
  if (!magia) return 0;

  if (magia.descricao) {
    const matchDice = magia.descricao.match(/(\d+)\s*d/);
    if (matchDice) {
      const dados = parseInt(matchDice[1], 10);
      if (!Number.isNaN(dados) && dados > 0) {
        return dados * 3;
      }
    }
  }

  const custo = obterCustoPmMagia(nome);
  return Math.max(1, custo);
}

