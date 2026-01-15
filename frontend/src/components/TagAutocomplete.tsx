import { useState, useCallback, type KeyboardEvent, useMemo } from 'react';
import { TagPill } from './TagPill';
import { Input } from '@/components/ui/input';
import type { TagWithCount } from '../types/prompt';

interface TagAutocompleteProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  availableTags: TagWithCount[];
  placeholder?: string;
  className?: string;
  tagClassName?: string;
  disabled?: boolean;
}

export function TagAutocomplete({
  tags,
  onChange,
  availableTags,
  placeholder = 'Add tags...',
  className = '',
  tagClassName = '',
  disabled = false,
}: TagAutocompleteProps) {
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  const suggestions = useMemo(() => {
    if (!inputValue.trim()) return [];
    const search = inputValue.toLowerCase();
    return availableTags
      .filter((t) => t.name.toLowerCase().includes(search) && !tags.includes(t.name))
      .slice(0, 5);
  }, [inputValue, availableTags, tags]);

  const addTag = useCallback(
    (tagText: string) => {
      if (disabled) return;
      const trimmedTag = tagText.trim();
      if (trimmedTag && !tags.includes(trimmedTag)) {
        onChange([...tags, trimmedTag]);
        setInputValue('');
        setShowSuggestions(false);
      }
    },
    [disabled, tags, onChange]
  );

  const removeTag = useCallback(
    (tagToRemove: string) => {
      if (disabled) return;
      onChange(tags.filter((tag) => tag !== tagToRemove));
    },
    [disabled, tags, onChange]
  );

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    setShowSuggestions(true);
  };

  const handleSuggestionClick = (tagName: string) => {
    addTag(tagName);
  };

  return (
    <div className="space-y-2 relative">
      <div className="relative">
        <Input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          placeholder={placeholder}
          className={className}
          disabled={disabled}
        />

        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-[var(--terminal-dark)] border border-[var(--terminal-border)] shadow-lg max-h-48 overflow-y-auto">
            {suggestions.map((tag) => (
              <button
                key={tag.name}
                type="button"
                className="w-full px-3 py-2 text-left text-sm text-[var(--terminal-text)] hover:bg-[var(--terminal-gray)] focus:bg-[var(--terminal-gray)] flex items-center justify-between"
                onMouseDown={() => handleSuggestionClick(tag.name)}
              >
                <span>{tag.name}</span>
                <span className="text-[var(--terminal-text-dim)] text-xs">({tag.count})</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <TagPill key={tag} tag={tag} onRemove={disabled ? undefined : () => removeTag(tag)} className={tagClassName} />
          ))}
        </div>
      )}
    </div>
  );
}
