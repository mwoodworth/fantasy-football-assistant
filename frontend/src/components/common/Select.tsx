import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, X } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  description?: string;
}

interface SelectProps {
  options: SelectOption[];
  value?: string | string[];
  onChange: (value: string | string[]) => void;
  placeholder?: string;
  multiple?: boolean;
  searchable?: boolean;
  disabled?: boolean;
  error?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  clearable?: boolean;
}

const selectSizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-3 py-2 text-sm',
  lg: 'px-4 py-3 text-base',
};

export function Select({
  options,
  value,
  onChange,
  placeholder = 'Select an option...',
  multiple = false,
  searchable = false,
  disabled = false,
  error,
  size = 'md',
  className,
  clearable = false
}: SelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const selectRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchable && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen, searchable]);

  const filteredOptions = searchable
    ? options.filter(option =>
        option.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        option.value.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;

  const selectedValues = Array.isArray(value) ? value : value ? [value] : [];
  const selectedOptions = options.filter(option => selectedValues.includes(option.value));

  const handleOptionClick = (option: SelectOption) => {
    if (option.disabled) return;

    if (multiple) {
      const currentValues = Array.isArray(value) ? value : [];
      const isSelected = currentValues.includes(option.value);
      
      if (isSelected) {
        onChange(currentValues.filter(v => v !== option.value));
      } else {
        onChange([...currentValues, option.value]);
      }
    } else {
      onChange(option.value);
      setIsOpen(false);
      setSearchTerm('');
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(multiple ? [] : '');
  };

  const getDisplayValue = () => {
    if (selectedOptions.length === 0) {
      return placeholder;
    }

    if (multiple) {
      if (selectedOptions.length === 1) {
        return selectedOptions[0].label;
      }
      return `${selectedOptions.length} selected`;
    }

    return selectedOptions[0].label;
  };

  const hasValue = multiple ? selectedValues.length > 0 : Boolean(value);

  return (
    <div className={cn('relative', className)} ref={selectRef}>
      {/* Select Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          'w-full flex items-center justify-between border border-gray-300 rounded-md bg-white',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
          selectSizes[size],
          disabled && 'bg-gray-50 text-gray-500 cursor-not-allowed',
          error && 'border-red-300 focus:ring-red-500 focus:border-red-500',
          hasValue ? 'text-gray-900' : 'text-gray-500'
        )}
      >
        <span className="block truncate">{getDisplayValue()}</span>
        
        <div className="flex items-center">
          {clearable && hasValue && !disabled && (
            <button
              onClick={handleClear}
              className="mr-2 p-1 text-gray-400 hover:text-gray-600 rounded"
            >
              <X className="w-3 h-3" />
            </button>
          )}
          <ChevronDown className={cn(
            'w-4 h-4 text-gray-400 transition-transform',
            isOpen && 'transform rotate-180'
          )} />
        </div>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {/* Search Input */}
          {searchable && (
            <div className="p-2 border-b border-gray-200">
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search options..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          )}

          {/* Options */}
          <div className="py-1">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500">
                {searchable && searchTerm ? 'No options found' : 'No options available'}
              </div>
            ) : (
              filteredOptions.map((option) => {
                const isSelected = selectedValues.includes(option.value);
                
                return (
                  <button
                    key={option.value}
                    onClick={() => handleOptionClick(option)}
                    disabled={option.disabled}
                    className={cn(
                      'w-full px-3 py-2 text-left text-sm flex items-center justify-between',
                      'hover:bg-gray-50 focus:outline-none focus:bg-gray-50',
                      option.disabled && 'text-gray-400 cursor-not-allowed',
                      isSelected && 'bg-primary-50 text-primary-700'
                    )}
                  >
                    <div className="flex-1">
                      <div className="font-medium">{option.label}</div>
                      {option.description && (
                        <div className="text-xs text-gray-500 mt-1">
                          {option.description}
                        </div>
                      )}
                    </div>
                    
                    {isSelected && (
                      <Check className="w-4 h-4 text-primary-600" />
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Multiple Selection Tags */}
      {multiple && selectedOptions.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {selectedOptions.map((option) => (
            <span
              key={option.value}
              className="inline-flex items-center px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded-full"
            >
              {option.label}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleOptionClick(option);
                }}
                className="ml-1 hover:text-primary-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}