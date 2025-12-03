import { Link, Outlet } from 'react-router-dom';
import { Moon, Sun, FileText, Plus } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

export function Layout() {
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem('theme');
    if (stored) {
      return stored === 'dark';
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (isDark) {
      root.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  return (
    <div className="min-h-screen bg-page transition-colors">
      <header className="bg-surface shadow-sm border-b border-default">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <FileText className="h-6 w-6 text-primary" />
                <span className="text-xl font-semibold text-default">
                  Prompt Manager
                </span>
              </Link>
            </div>
            
            <nav className="flex items-center space-x-4">
              <Button variant="ghost" asChild>
                <Link to="/">Prompts</Link>
              </Button>
              <Button asChild>
                <Link to="/new">
                  <Plus className="h-4 w-4" />
                  <span>New Prompt</span>
                </Link>
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                aria-label="Toggle theme"
              >
                {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
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