import { useState, useMemo } from 'react';
import { Input } from '@/components/ui/input';

interface GroupSelectProps {
  value: string;
  onChange: (value: string) => void;
  availableGroups: string[];
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export function GroupSelect({
  value,
  onChange,
  availableGroups,
  placeholder = 'Select or enter group...',
  className = '',
  disabled = false,
}: GroupSelectProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);

  const suggestions = useMemo(() => {
    if (!value.trim()) return availableGroups;
    const search = value.toLowerCase();
    return availableGroups.filter((g) => g.toLowerCase().includes(search));
  }, [value, availableGroups]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
    setShowSuggestions(true);
  };

  const handleSuggestionClick = (group: string) => {
    onChange(group);
    setShowSuggestions(false);
  };

  return (
    <div className="relative">
      <Input
        type="text"
        value={value}
        onChange={handleInputChange}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        placeholder={placeholder}
        className={className}
        disabled={disabled}
      />

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-[var(--terminal-dark)] border border-[var(--terminal-border)] shadow-lg max-h-48 overflow-y-auto">
          {suggestions.map((group) => (
            <button
              key={group}
              type="button"
              className="w-full px-3 py-2 text-left text-sm text-[var(--terminal-text)] hover:bg-[var(--terminal-gray)] focus:bg-[var(--terminal-gray)]"
              onMouseDown={() => handleSuggestionClick(group)}
            >
              {group}
            </button>
          ))}
          {value.trim() && !availableGroups.includes(value.trim()) && (
            <button
              type="button"
              className="w-full px-3 py-2 text-left text-sm text-[var(--terminal-green)] hover:bg-[var(--terminal-gray)] focus:bg-[var(--terminal-gray)] border-t border-[var(--terminal-border)]"
              onMouseDown={() => handleSuggestionClick(value.trim())}
            >
              + Create "{value.trim()}"
            </button>
          )}
        </div>
      )}
    </div>
  );
}
