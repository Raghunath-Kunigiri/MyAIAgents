import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Check } from 'lucide-react';
import { JobStatus } from '../types';

interface StatusDropdownProps {
  value: JobStatus | null;
  onChange: (status: JobStatus) => void;
  disabled?: boolean;
}

const statusOptions: { value: JobStatus; label: string; color: string }[] = [
  { value: 'Interested', label: 'Interested', color: 'bg-blue-100 text-blue-700' },
  { value: 'Applied', label: 'Applied', color: 'bg-indigo-100 text-indigo-700' },
  { value: 'Screening Call', label: 'Screening Call', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'Interviewing', label: 'Interviewing', color: 'bg-purple-100 text-purple-700' },
  { value: 'Offer', label: 'Offer', color: 'bg-emerald-100 text-emerald-700' },
  { value: 'Rejected', label: 'Rejected', color: 'bg-rose-100 text-rose-700' },
  { value: 'Not Interested', label: 'Not Interested', color: 'bg-gray-100 text-gray-700' },
];

const getStatusColor = (status: JobStatus | null): string => {
  if (!status) return 'bg-gray-100 text-gray-600';
  const option = statusOptions.find(opt => opt.value === status);
  return option?.color || 'bg-gray-100 text-gray-600';
};

export function StatusDropdown({ value, onChange, disabled = false }: StatusDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = statusOptions.find(opt => opt.value === value);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full min-w-[160px] px-3 py-2 rounded-lg text-sm font-medium
          border-2 transition-all duration-200 flex items-center justify-between gap-2
          ${disabled
            ? 'opacity-60 cursor-not-allowed bg-gray-50 border-gray-200 text-gray-500'
            : isOpen
              ? 'border-indigo-500 ring-2 ring-indigo-200 bg-white'
              : 'border-gray-200 hover:border-indigo-300 bg-white'
          }
        `}
      >
        <span className={value ? getStatusColor(value).split(' ')[1] : 'text-gray-500'}>
          {selectedOption?.label || 'Select Status'}
        </span>
        <ChevronDown
          className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute z-50 mt-2 w-full bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden"
          >
            <div className="py-1 max-h-64 overflow-y-auto">
              {statusOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                  }}
                  className={`
                    w-full px-4 py-2.5 text-left text-sm font-medium
                    flex items-center justify-between
                    transition-colors duration-150
                    ${value === option.value
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-gray-700 hover:bg-gray-50'
                    }
                  `}
                >
                  <span>{option.label}</span>
                  {value === option.value && (
                    <Check className="w-4 h-4 text-indigo-600" />
                  )}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
