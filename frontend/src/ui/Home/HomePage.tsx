/**
 * Tela inicial — seleção de personagem e acesso ao jogo.
 * Personagens salvos ficam disponíveis para uso nos testes.
 * Estrutura preparada para multi-jogador: userId em PersonagemSalvo (futuro login).
 */

import { Link, useNavigate } from "react-router-dom";
import { usePersonagensStore } from "@/store/personagensStore";
import { BarraVital } from "@/ui/Bestiario/BarraVital";
import { CaracteristicasComIcones } from "@/ui/Bestiario/CaracteristicasComIcones";

export function HomePage() {
  const navigate = useNavigate();
  const { personagens, personagemAtivoId, setPersonagemAtivo, removePersonagem } =
    usePersonagensStore();

  const handleSelecionar = (id: string) => {
    setPersonagemAtivo(id);
  };

  const handleEditar = (id: string) => {
    navigate(`/ficha/editar/${id}`);
  };

  const handleExcluir = (id: string) => {
    if (window.confirm("Excluir este personagem? Esta ação não pode ser desfeita.")) {
      removePersonagem(id);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-stone-800">3D&T Idle RPG</h1>
        <p className="mt-2 text-stone-600">
          Bem-vindo ao sistema de jogo Idle baseado nas regras de 3D&T Alpha.
        </p>
      </div>

      {/* Seção: Meus Personagens */}
      <section className="rounded-xl border-2 border-stone-300 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-stone-800">Meus Personagens</h2>
          <Link
            to="/ficha"
            className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 font-medium text-white hover:bg-amber-600"
          >
            + Criar novo personagem
          </Link>
        </div>

        {personagens.length === 0 ? (
          <div className="rounded-lg border-2 border-dashed border-stone-300 bg-stone-50 p-8 text-center">
            <p className="text-stone-600">
              Nenhum personagem criado ainda.{' '}
              <Link to="/ficha" className="font-medium text-amber-600 hover:text-amber-700">
                Crie sua primeira ficha
              </Link>
              {' '}e salve para começar a jogar.
            </p>
          </div>
        ) : (
          <ul className="space-y-2">
            {personagens.map((p) => {
              const ativo = p.id === personagemAtivoId;
              const nome = p.ficha.nome || "(Sem nome)";
              const raca = p.ficha.raca || "—";
              const nivelLabel: Record<string, string> = {
                pessoa_comum: "Pessoa Comum",
                novato: "Novato",
                lutador: "Lutador",
                campeao: "Campeão",
                lenda: "Lenda",
              };
              const nivel = nivelLabel[p.ficha.nivelPontuacao] || p.ficha.nivelPontuacao;

              return (
                <li
                  key={p.id}
                  className={`flex flex-wrap items-center justify-between gap-3 rounded-lg border-2 p-4 transition ${
                    ativo
                      ? "border-amber-500 bg-amber-50"
                      : "border-stone-200 bg-stone-50/50 hover:border-amber-300"
                  }`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-stone-800">{nome}</span>
                      {ativo && (
                        <span className="rounded bg-amber-200 px-2 py-0.5 text-xs font-medium text-amber-800">
                          Em uso
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-sm text-stone-500">
                      {raca} {nivel && `• ${nivel}`}
                    </p>
                    <div className="mt-2 flex flex-wrap items-center gap-3">
                      <BarraVital
                        valor={`${p.ficha.pvAtual}/${p.ficha.pvMax}`}
                        tipo="pv"
                        altura={12}
                      />
                      <BarraVital
                        valor={`${p.ficha.pmAtual}/${p.ficha.pmMax}`}
                        tipo="pm"
                        altura={12}
                      />
                      <div className="flex flex-wrap items-center gap-1.5 text-xs">
                        <CaracteristicasComIcones
                          caracteristicas={
                            p.ficha.caracteristicas
                              ? {
                                  F: String(p.ficha.caracteristicas.F),
                                  H: String(p.ficha.caracteristicas.H),
                                  R: String(p.ficha.caracteristicas.R),
                                  A: String(p.ficha.caracteristicas.A),
                                  PdF: String(p.ficha.caracteristicas.PdF),
                                }
                              : undefined
                          }
                          className="text-xs font-medium tabular-nums text-stone-700"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-shrink-0 gap-2">
                    <button
                      type="button"
                      onClick={() => handleSelecionar(p.id)}
                      disabled={ativo}
                      className={`rounded px-3 py-1.5 text-sm font-medium ${
                        ativo
                          ? "cursor-default bg-amber-200 text-amber-800"
                          : "bg-amber-100 text-amber-800 hover:bg-amber-200"
                      }`}
                    >
                      {ativo ? "Selecionado" : "Usar"}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleEditar(p.id)}
                      className="rounded border border-stone-300 px-3 py-1.5 text-sm text-stone-600 hover:bg-stone-100"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => handleExcluir(p.id)}
                      className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50"
                    >
                      Excluir
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* Links rápidos */}
      <section className="flex flex-wrap gap-3">
        <Link
          to="/bestiario"
          className="inline-block rounded-lg bg-amber-500 px-6 py-3 font-medium text-white hover:bg-amber-600"
        >
          Abrir Bestiário
        </Link>
        <Link
          to="/itens"
          className="inline-block rounded-lg border border-amber-500 px-6 py-3 font-medium text-amber-700 hover:bg-amber-50"
        >
          Ver todos os itens
        </Link>
      </section>
    </div>
  );
}
