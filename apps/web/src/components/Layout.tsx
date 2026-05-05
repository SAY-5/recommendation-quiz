import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-bean-50 text-bean-900">
      <header className="border-b border-bean-100 bg-white/70 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-lg font-semibold text-bean-700">
            Coffee Quiz
          </Link>
          <span className="text-xs uppercase tracking-wider text-bean-500">
            recommendation engine
          </span>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-6 sm:py-10">{children}</main>
      <footer className="mx-auto max-w-3xl px-4 pb-8 text-center text-xs text-bean-500">
        Open source under MIT.
      </footer>
    </div>
  );
}
