import { Link, Outlet, useLocation } from 'react-router-dom';
import { Terminal, Plus } from 'lucide-react';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export function Layout() {
  const location = useLocation();

  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  return (
    <div className="min-h-screen bg-page">
      <header className="terminal-header border-b border-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14">
            <div className="flex items-center">
              <Link to="/" className="flex items-center gap-3 group">
                <div className="flex items-center justify-center w-8 h-8 border border-primary text-primary group-hover:bg-primary group-hover:text-black transition-all">
                  <Terminal className="h-4 w-4" />
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-primary glow-green tracking-wider">
                    PROMPT_BUTLER
                  </span>
                  <span className="text-[10px] text-muted-foreground tracking-widest">
                    v1.0.0
                  </span>
                </div>
              </Link>
            </div>
            
            <nav className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                asChild
                className={location.pathname === '/' ? 'border-primary text-primary' : ''}
              >
                <Link to="/">[PROMPTS]</Link>
              </Button>
              <Button size="sm" asChild>
                <Link to="/new">
                  <Plus className="h-3 w-3" />
                  <span>NEW</span>
                </Link>
              </Button>
            </nav>
          </div>
        </div>

        <div className="border-t border-border bg-surface">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-6 text-[10px] text-muted-foreground tracking-wider">
              <div className="flex items-center gap-4">
                <span className="text-primary">●</span>
                <span>SYS:ONLINE</span>
                <span className="text-border">│</span>
                <span>MEM:OK</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-accent">PATH:</span>
                <span className="text-foreground">{location.pathname}</span>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-16">
        <Outlet />
      </main>

      <footer className="fixed bottom-0 left-0 right-0 border-t border-border bg-surface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-8 text-[10px] text-muted-foreground tracking-widest">
            <span className="text-primary">■</span>
            <span className="mx-2">PROMPT_BUTLER</span>
            <span className="text-border">│</span>
            <span className="mx-2">TERMINAL_INTERFACE</span>
            <span className="text-border">│</span>
            <span className="mx-2 text-accent">2024</span>
            <span className="text-primary">■</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
