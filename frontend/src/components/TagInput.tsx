import { useState, type KeyboardEvent, type FocusEvent } from 'react';
import { TagPill } from './TagPill';

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  className?: string;
}

export function TagInput({ tags, onChange, placeholder = 'Add tags...', className = '' }: TagInputProps) {
  const [inputValue, setInputValue] = useState('');

  const addTag = (tagText: string) => {
    const trimmedTag = tagText.trim();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      onChange([...tags, trimmedTag]);
      setInputValue('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    onChange(tags.filter(tag => tag !== tagToRemove));
  };

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
    <div className={`space-y-2 ${className}`}>
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        placeholder={placeholder}
        className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
      
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <TagPill
              key={tag}
              tag={tag}
              onRemove={() => removeTag(tag)}
            />
          ))}
        </div>
      )}
    </div>
  );
}