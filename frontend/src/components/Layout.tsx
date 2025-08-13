import { Link, Outlet } from 'react-router-dom';
import { Moon, Sun, FileText, Plus } from 'lucide-react';
import { useState, useEffect } from 'react';

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
    <div className="min-h-screen bg-secondary transition-colors">
      <header className="bg-primary shadow-sm border-b border-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <FileText className="h-6 w-6 text-blue-600" />
                <span className="text-xl font-semibold text-primary">
                  Prompt Manager
                </span>
              </Link>
            </div>
            
            <nav className="flex items-center space-x-4">
              <Link
                to="/"
                className="text-secondary hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Prompts
              </Link>
              <Link
                to="/new"
                className="flex items-center space-x-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>New Prompt</span>
              </Link>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md text-secondary hover:bg-tertiary transition-colors"
                aria-label="Toggle theme"
              >
                {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
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