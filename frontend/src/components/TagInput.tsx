import { useState, useCallback, useEffect, useRef, type KeyboardEvent, type FocusEvent } from 'react';
import { TagPill } from './TagPill';
import { Input } from '@/components/ui/input';
import { tagApi } from '../services/api';

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  className?: string;
  tagClassName?: string;
  disabled?: boolean;
}

export function TagInput({ tags, onChange, placeholder = 'Add tags...', className = '', tagClassName = '', disabled = false }: TagInputProps) {
  const [inputValue, setInputValue] = useState('');
  const [allTags, setAllTags] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Fetch all tags on mount
  useEffect(() => {
    tagApi.listTags()
      .then(tagCounts => {
        setAllTags(tagCounts.map(tc => tc.tag));
      })
      .catch(console.error);
  }, []);

  // Update suggestions when input changes
  useEffect(() => {
    const trimmedInput = inputValue.trim();
    if (!trimmedInput) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const query = trimmedInput.toLowerCase();
    const filtered = allTags
      .filter(tag =>
        tag.toLowerCase().includes(query) &&
        !tags.includes(tag)
      )
      .slice(0, 8);

    setSuggestions(filtered);
    const canCreate = !allTags.includes(trimmedInput) && !tags.includes(trimmedInput);
    setShowSuggestions(filtered.length > 0 || canCreate);
    setHighlightedIndex(-1);
  }, [inputValue, allTags, tags]);

  const addTag = useCallback((tagText: string) => {
    if (disabled) return;
    const trimmedTag = tagText.trim();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      onChange([...tags, trimmedTag]);
      setInputValue('');
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [disabled, tags, onChange]);

  const removeTag = useCallback((tagToRemove: string) => {
    if (disabled) return;
    onChange(tags.filter(tag => tag !== tagToRemove));
  }, [disabled, tags, onChange]);

  const selectSuggestion = useCallback((tag: string) => {
    addTag(tag);
    inputRef.current?.focus();
  }, [addTag]);

  const trimmedInput = inputValue.trim();
  const canCreate = trimmedInput.length > 0 && !allTags.includes(trimmedInput) && !tags.includes(trimmedInput);
  const totalOptions = suggestions.length + (canCreate ? 1 : 0);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (highlightedIndex >= 0 && suggestions[highlightedIndex]) {
        selectSuggestion(suggestions[highlightedIndex]);
      } else if (highlightedIndex === suggestions.length && canCreate) {
        addTag(inputValue);
      } else if (inputValue.trim()) {
        addTag(inputValue);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (showSuggestions) {
        setHighlightedIndex(prev =>
          prev < totalOptions - 1 ? prev + 1 : prev
        );
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (showSuggestions) {
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : -1);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setHighlightedIndex(-1);
    } else if (e.key === 'Tab' && showSuggestions && highlightedIndex >= 0) {
      e.preventDefault();
      if (highlightedIndex === suggestions.length && canCreate) {
        addTag(inputValue);
      } else {
        selectSuggestion(suggestions[highlightedIndex]);
      }
    }
  };

  const handleBlur = (e: FocusEvent<HTMLInputElement>) => {
    // Delay hiding to allow clicking on suggestions
    setTimeout(() => {
      if (!suggestionsRef.current?.contains(document.activeElement)) {
        setShowSuggestions(false);
        if (e.target.value.trim()) {
          addTag(e.target.value);
        }
      }
    }, 150);
  };

  const handleFocus = () => {
    if (inputValue.trim() && (suggestions.length > 0 || canCreate)) {
      setShowSuggestions(true);
    }
  };

  return (
    <div className="space-y-2 relative">
      <div className="relative">
        <Input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          onFocus={handleFocus}
          placeholder={placeholder}
          className={className}
          disabled={disabled}
          autoComplete="off"
        />

        {showSuggestions && (
          <div
            ref={suggestionsRef}
            className="absolute z-50 w-full mt-1 terminal-panel max-h-48 overflow-auto"
          >
            {suggestions.map((tag, index) => (
              <button
                key={tag}
                type="button"
                className={`w-full px-3 py-2 text-left text-xs tracking-wider hover:bg-surface-alt focus:bg-surface-alt focus:outline-none ${
                  index === highlightedIndex ? 'bg-surface-alt text-primary' : 'text-foreground'
                }`}
                onMouseDown={(e) => {
                  e.preventDefault();
                  selectSuggestion(tag);
                }}
                onMouseEnter={() => setHighlightedIndex(index)}
              >
                <span className="text-default">{tag}</span>
              </button>
            ))}
            {canCreate && (
              <button
                type="button"
                className={`w-full px-3 py-2 text-left text-xs tracking-wider hover:bg-surface-alt focus:bg-surface-alt focus:outline-none border-t border-border ${
                  highlightedIndex === suggestions.length ? 'bg-surface-alt text-primary' : 'text-foreground'
                }`}
                onMouseDown={(e) => {
                  e.preventDefault();
                  addTag(inputValue);
                }}
              >
                <span className="text-muted-foreground">Create new tag: </span>
                <span className="font-medium">{inputValue.trim()}</span>
              </button>
            )}
          </div>
        )}
      </div>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <TagPill
              key={tag}
              tag={tag}
              onRemove={disabled ? undefined : () => removeTag(tag)}
              className={tagClassName}
            />
          ))}
        </div>
      )}
    </div>
  );
}
