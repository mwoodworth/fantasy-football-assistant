import { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '../../utils/cn';

interface PlayerSearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  className?: string;
}

export function PlayerSearchInput({
  value,
  onChange,
  placeholder = 'Search players...',
  disabled = false,
  autoFocus = false,
  className
}: PlayerSearchInputProps) {
  const [localValue, setLocalValue] = useState(value);

  // Update local value when prop value changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  // Debounce the search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localValue !== value) {
        onChange(localValue);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [localValue, value, onChange]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalValue(e.target.value);
  };

  const handleClear = () => {
    setLocalValue('');
    onChange('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClear();
    }
  };

  return (
    <div className={cn('relative', className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        
        <input
          type="text"
          value={localValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          autoFocus={autoFocus}
          className={cn(
            'w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder:text-gray-400',
            'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
            'transition-colors'
          )}
        />
        
        {localValue && (
          <button
            onClick={handleClear}
            disabled={disabled}
            className={cn(
              'absolute right-3 top-1/2 transform -translate-y-1/2',
              'p-1 rounded-md text-gray-400 hover:text-gray-600',
              'disabled:cursor-not-allowed',
              'transition-colors'
            )}
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      
      {/* Search suggestions could go here */}
      {localValue && localValue.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 text-xs text-gray-500 px-3">
          Press Enter to search or wait for auto-search
        </div>
      )}
    </div>
  );
}