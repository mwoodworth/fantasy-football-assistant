import type { ReactNode } from 'react';
import { useState } from 'react';
import { ChevronUp, ChevronDown, MoreHorizontal } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface Column<T = any> {
  key: string;
  header: string | ReactNode;
  accessor?: keyof T | ((row: T) => any);
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, row: T, index: number) => ReactNode;
}

export interface TableProps<T = any> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  emptyMessage?: string;
  striped?: boolean;
  hoverable?: boolean;
  compact?: boolean;
  onRowClick?: (row: T, index: number) => void;
  className?: string;
  sortable?: boolean;
  defaultSort?: { key: string; direction: 'asc' | 'desc' };
}

export function Table<T = any>({
  data,
  columns,
  loading = false,
  emptyMessage = 'No data available',
  striped = false,
  hoverable = true,
  compact = false,
  onRowClick,
  className,
  sortable = true,
  defaultSort
}: TableProps<T>) {
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(defaultSort || null);

  const getCellValue = (row: T, column: Column<T>) => {
    if (column.accessor) {
      if (typeof column.accessor === 'function') {
        return column.accessor(row);
      }
      return row[column.accessor];
    }
    return (row as any)[column.key];
  };

  const handleSort = (column: Column<T>) => {
    if (!sortable || !column.sortable) return;

    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === column.key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }

    setSortConfig({ key: column.key, direction });
  };

  const sortedData = [...data];
  if (sortConfig) {
    sortedData.sort((a, b) => {
      const column = columns.find(col => col.key === sortConfig.key);
      if (!column) return 0;

      const aValue = getCellValue(a, column);
      const bValue = getCellValue(b, column);

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }

  const getSortIcon = (column: Column<T>) => {
    if (!sortable || !column.sortable) return null;
    
    if (!sortConfig || sortConfig.key !== column.key) {
      return (
        <div className="flex flex-col ml-1">
          <ChevronUp className="w-3 h-3 text-gray-300" />
          <ChevronDown className="w-3 h-3 text-gray-300 -mt-1" />
        </div>
      );
    }

    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="w-4 h-4 ml-1 text-gray-600" />
    ) : (
      <ChevronDown className="w-4 h-4 ml-1 text-gray-600" />
    );
  };

  if (loading) {
    return (
      <div className="w-full">
        <div className="animate-pulse">
          <div className="h-12 bg-gray-200 rounded mb-2"></div>
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 bg-gray-100 rounded mb-2"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="w-full border border-gray-200 rounded-lg">
        <div className="text-center py-12 text-gray-500">
          {emptyMessage}
        </div>
      </div>
    );
  }

  return (
    <div className={cn('w-full overflow-hidden border border-gray-200 rounded-lg', className)}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    'px-6 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                    compact ? 'py-2' : 'py-3',
                    column.sortable && sortable && 'cursor-pointer hover:bg-gray-100',
                    column.align === 'center' && 'text-center',
                    column.align === 'right' && 'text-right'
                  )}
                  style={{ width: column.width }}
                  onClick={() => handleSort(column)}
                >
                  <div className="flex items-center">
                    {column.header}
                    {getSortIcon(column)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedData.map((row, index) => (
              <tr
                key={index}
                className={cn(
                  striped && index % 2 === 1 && 'bg-gray-50',
                  hoverable && 'hover:bg-gray-50',
                  onRowClick && 'cursor-pointer',
                  'transition-colors'
                )}
                onClick={() => onRowClick?.(row, index)}
              >
                {columns.map((column) => {
                  const value = getCellValue(row, column);
                  const renderedValue = column.render ? column.render(value, row, index) : value;

                  return (
                    <td
                      key={column.key}
                      className={cn(
                        'px-6 whitespace-nowrap text-sm text-gray-900',
                        compact ? 'py-2' : 'py-4',
                        column.align === 'center' && 'text-center',
                        column.align === 'right' && 'text-right'
                      )}
                    >
                      {renderedValue}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Table Actions Component
interface TableActionsProps {
  children: ReactNode;
  className?: string;
}

export function TableActions({ children, className }: TableActionsProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={cn('relative inline-block text-left', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
      >
        <MoreHorizontal className="w-4 h-4" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 z-20 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200">
            <div className="py-1">
              {children}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Table Action Item
interface TableActionItemProps {
  onClick: () => void;
  children: ReactNode;
  icon?: ReactNode;
  variant?: 'default' | 'danger';
}

export function TableActionItem({ 
  onClick, 
  children, 
  icon, 
  variant = 'default' 
}: TableActionItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center',
        variant === 'danger' ? 'text-red-600 hover:bg-red-50' : 'text-gray-700'
      )}
    >
      {icon && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
}