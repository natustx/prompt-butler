import { Link, Outlet } from 'react-router-dom';
import { Terminal, Plus } from 'lucide-react';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export function Layout() {
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.add('dark');
  }, []);

  return (
    <div className="min-h-screen bg-[var(--terminal-black)] scanlines">
      <header className="bg-[var(--terminal-dark)] border-b border-[var(--terminal-border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-3 group">
                <Terminal className="h-6 w-6 text-[var(--terminal-green)] group-hover:drop-shadow-[0_0_8px_var(--terminal-green)] transition-all" />
                <span className="text-xl font-semibold text-[var(--terminal-green)] crt-glow tracking-wider">
                  PROMPT_BUTLER
                </span>
              </Link>
            </div>

            <nav className="flex items-center space-x-4">
              <Button variant="ghost" asChild>
                <Link to="/">&gt; LIST</Link>
              </Button>
              <Button asChild>
                <Link to="/new">
                  <Plus className="h-4 w-4" />
                  <span>NEW</span>
                </Link>
              </Button>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}