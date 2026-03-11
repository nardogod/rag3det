import type { Monstro } from "@/types/monstro";
import type {
  AcaoMonstro,
  EstadoBatalha,
  TipoAcaoBasica,
} from "./types";
import { parseNumeroSimples } from "./formulas";

function escolherTipoAtaqueBasico(monstro: Monstro): TipoAcaoBasica {
  const c = monstro.caracteristicas || {};
  const f = parseNumeroSimples(c.F);
  const pdf = parseNumeroSimples(c.PdF);
  if (pdf > f) return "ataque_distancia";
  return "ataque_corpo_a_corpo";
}

export function decidirAcaoMonstro(
  estado: EstadoBatalha,
  monstroDados: Monstro
): AcaoMonstro {
  const monstro = estado.monstro;
  const jogador = estado.jogador;

  if (monstro.pvAtual < monstro.pvMax / 3 && jogador.pvAtual > monstro.pvAtual) {
    return {
      lado: "monstro",
      tipo: escolherTipoAtaqueBasico(monstroDados),
    };
  }

  const tipo = escolherTipoAtaqueBasico(monstroDados);

  const ataques = monstroDados.ataques_especificos ?? [];
  const ataqueMaisForte = ataques[0];

  return {
    lado: "monstro",
    tipo,
    ataqueEspecifico: ataqueMaisForte?.nome,
  };
}

