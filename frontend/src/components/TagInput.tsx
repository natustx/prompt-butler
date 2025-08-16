import { useState, useCallback, type KeyboardEvent, type FocusEvent } from 'react';
import { TagPill } from './TagPill';

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

  const addTag = useCallback((tagText: string) => {
    if (disabled) return;
    const trimmedTag = tagText.trim();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      onChange([...tags, trimmedTag]);
      setInputValue('');
    }
  }, [disabled, tags, onChange]);

  const removeTag = useCallback((tagToRemove: string) => {
    if (disabled) return;
    onChange(tags.filter(tag => tag !== tagToRemove));
  }, [disabled, tags, onChange]);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag(inputValue);
    }
  };

  const handleBlur = (e: FocusEvent<HTMLInputElement>) => {
    addTag(e.target.value);
  };

  return (
    <div className="space-y-2">
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        placeholder={placeholder}
        className={className}
        disabled={disabled}
      />
      
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