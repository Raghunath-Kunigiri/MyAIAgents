import { motion } from 'framer-motion';
import { JobStatus } from '../types';

interface FilterBadgeProps {
  label: string;
  count: number;
  isActive: boolean;
  onClick: () => void;
  status: JobStatus;
}

export function FilterBadge({ label, count, isActive, onClick, status }: FilterBadgeProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        px-5 py-2.5 rounded-full font-semibold text-sm
        transition-all duration-300 flex items-center gap-2
        ${isActive
          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/30'
          : 'bg-white text-gray-700 border-2 border-gray-200 hover:border-indigo-300 hover:bg-indigo-50/50'
        }
      `}
    >
      <span>{label}</span>
      <span
        className={`
          min-w-[26px] h-6 px-2 rounded-full text-xs font-bold flex items-center justify-center
          ${isActive
            ? 'bg-white/30 text-white'
            : 'bg-gray-100 text-gray-600'
          }
        `}
      >
        {count}
      </span>
    </motion.button>
  );
}
