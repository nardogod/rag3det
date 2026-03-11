import { Link } from "react-router-dom";
import type { Monstro } from "@/types/monstro";
import { formatarFichaMonstro } from "@/core/bestiario";
import {
  calcularForcaMonstro,
  labelForca,
  badgeForca,
} from "@/core/forcaMonstro";
import { BarraVital } from "./BarraVital";
import { CaracteristicasComIcones } from "./CaracteristicasComIcones";
import { TextoComHabilidadesClicaveis } from "@/ui/HabilidadesMonstros/TextoComHabilidadesClicaveis";

interface FichaMonstroProps {
  monstro: Monstro;
  livroSlug?: string | null;
}

function CelulaValor({
  campo,
  valor,
  monstro,
}: {
  campo: string;
  valor: string;
  monstro: Monstro;
}) {
  if (campo === "PV / PM") {
    const [pv, pm] = valor.split(/\s*\/\s*/).map((s) => s.trim());
    return (
      <div className="flex flex-col gap-2 sm:flex-row sm:gap-4">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-stone-500">PV</span>
          <BarraVital valor={pv || "—"} tipo="pv" />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-stone-500">PM</span>
          <BarraVital valor={pm || "—"} tipo="pm" />
        </div>
      </div>
    );
  }
  if (campo === "Características") {
    return <CaracteristicasComIcones caracteristicas={monstro.caracteristicas} />;
  }
  if (valor && valor !== "—") {
    return (
      <TextoComHabilidadesClicaveis
        texto={valor}
        className="inline"
      />
    );
  }
  return <>{valor || "—"}</>;
}

export function FichaMonstro({ monstro, livroSlug }: FichaMonstroProps) {
  const linhas = formatarFichaMonstro(monstro);
  const basePath = livroSlug
    ? `/bestiario/livro/${livroSlug}`
    : "/bestiario";

  const forca = calcularForcaMonstro(monstro);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <h2 className="text-2xl font-bold text-stone-800">{monstro.nome}</h2>
          <div className="flex items-center gap-3">
            <BarraVital valor={monstro.pv ?? "—"} tipo="pv" />
            <BarraVital valor={monstro.pm ?? "—"} tipo="pm" />
            <span
              className={`rounded px-2 py-0.5 text-sm font-semibold ${badgeForca(forca)}`}
              title={labelForca(forca)}
            >
              Força: {forca}
            </span>
          </div>
        </div>
        <Link
          to={basePath || "/bestiario"}
          className="text-sm text-amber-600 hover:text-amber-700"
        >
          ← Voltar à lista
        </Link>
      </div>

      <div className="overflow-x-auto rounded-lg border border-stone-300 bg-white shadow-sm">
        <table className="w-full min-w-[320px] text-left text-sm">
          <thead>
            <tr className="border-b border-stone-200 bg-stone-50">
              <th className="px-4 py-2 font-semibold text-stone-700">
                Campo
              </th>
              <th className="px-4 py-2 font-semibold text-stone-700">
                Valor
              </th>
            </tr>
          </thead>
          <tbody>
            {linhas.map(({ campo, valor }) => (
              <tr
                key={campo}
                className="border-b border-stone-100 last:border-0"
              >
                <td className="w-1/3 px-4 py-2 font-medium text-stone-600">
                  {campo}
                </td>
                <td className="px-4 py-2 text-stone-700">
                  <CelulaValor campo={campo} valor={valor} monstro={monstro} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {monstro.descricao && (
        <div className="rounded-lg border border-stone-300 bg-white p-4">
          <h3 className="mb-2 font-semibold text-stone-700">Descrição</h3>
          <p className="whitespace-pre-wrap text-stone-600">
            <TextoComHabilidadesClicaveis texto={monstro.descricao} />
          </p>
        </div>
      )}
    </div>
  );
}
