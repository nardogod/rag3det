import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "@/ui/Layout/AppLayout";
import { HomePage } from "@/ui/Home/HomePage";

// Lazy load: monstros.json (2.4MB) só carrega ao abrir Bestiário
const BestiarioPage = lazy(() =>
  import("@/ui/Bestiario/BestiarioPage").then((m) => ({ default: m.BestiarioPage }))
);
const FichaPersonagemPage = lazy(() =>
  import("@/ui/FichaPersonagem/FichaPersonagemPage").then((m) => ({
    default: m.FichaPersonagemPage,
  }))
);
const HabilidadesMonstrosPage = lazy(() =>
  import("@/ui/HabilidadesMonstros/HabilidadesMonstrosPage").then((m) => ({
    default: m.HabilidadesMonstrosPage,
  }))
);
const ItensPage = lazy(() =>
  import("@/ui/Itens/ItensPage").then((m) => ({ default: m.ItensPage }))
);
const CombatPage = lazy(() =>
  import("@/ui/Combate/CombatPage").then((m) => ({ default: m.CombatPage }))
);

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<HomePage />} />
          <Route
            path="bestiario"
            element={
              <Suspense fallback={<div className="p-4 text-stone-600">Carregando Bestiário…</div>}>
                <BestiarioPage />
              </Suspense>
            }
          />
          <Route
            path="bestiario/livro/:livroSlug"
            element={
              <Suspense fallback={<div className="p-4 text-stone-600">Carregando…</div>}>
                <BestiarioPage />
              </Suspense>
            }
          />
          <Route
            path="bestiario/livro/:livroSlug/monstro/:monstroSlug"
            element={
              <Suspense fallback={<div className="p-4 text-stone-600">Carregando…</div>}>
                <BestiarioPage />
              </Suspense>
            }
          />
          <Route
            path="itens"
            element={
              <Suspense fallback={<div className="p-4 text-stone-600">Carregando Itens…</div>}>
                <ItensPage />
              </Suspense>
            }
          />
          <Route
            path="habilidades"
            element={
              <Suspense fallback={<div className="p-4 text-stone-600">Carregando Habilidades…</div>}>
                <HabilidadesMonstrosPage />
              </Suspense>
            }
          />
          <Route
            path="ficha"
            element={
              <Suspense fallback={<div className="p-4 text-stone-600">Carregando Ficha…</div>}>
                <FichaPersonagemPage />
              </Suspense>
            }
          />
          <Route
            path="ficha/editar/:personagemId"
            element={
              <Suspense fallback={<div className="p-4 text-stone-600">Carregando Ficha…</div>}>
                <FichaPersonagemPage />
              </Suspense>
            }
          />
          <Route
            path="combate"
            element={
              <Suspense fallback={<div className="p-4 text-stone-600">Carregando Combate…</div>}>
                <CombatPage />
              </Suspense>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
