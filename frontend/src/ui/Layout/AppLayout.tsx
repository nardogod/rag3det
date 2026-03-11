import { Outlet, Link } from "react-router-dom";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-stone-100 text-stone-900">
      <header className="border-b border-stone-300 bg-stone-200 px-4 py-3">
        <nav className="flex items-center gap-4">
          <Link
            to="/"
            className="font-semibold text-stone-800 hover:text-amber-700"
          >
            3D&T Idle
          </Link>
          <Link
            to="/combate"
            className="text-stone-600 hover:text-amber-700"
          >
            Combate
          </Link>
          <Link
            to="/bestiario"
            className="text-stone-600 hover:text-amber-700"
          >
            Bestiário
          </Link>
          <Link
            to="/itens"
            className="text-stone-600 hover:text-amber-700"
          >
            Itens
          </Link>
          <Link
            to="/habilidades"
            className="text-stone-600 hover:text-amber-700"
          >
            Habilidades
          </Link>
          <Link
            to="/ficha"
            className="text-stone-600 hover:text-amber-700"
          >
            Ficha
          </Link>
        </nav>
      </header>
      <main className="p-4 sm:p-6">
        <Outlet />
      </main>
    </div>
  );
}
