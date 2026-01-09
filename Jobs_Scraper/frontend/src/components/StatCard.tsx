import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  variant?: 'default' | 'success';
  className?: string;
}

export function StatCard({ label, value, icon: Icon, variant = 'default', className = '' }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className={`
        relative bg-white rounded-2xl p-7 border border-gray-200 
        shadow-sm hover:shadow-lg transition-all duration-300
        overflow-hidden group
        ${className}
      `}
    >
      {/* Gradient top border */}
      <div
        className={`
          absolute top-0 left-0 right-0 h-1 
          ${variant === 'success' 
            ? 'bg-gradient-to-r from-emerald-500 to-emerald-600' 
            : 'bg-gradient-to-r from-indigo-500 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity'
          }
        `}
      />
      
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            {label}
          </p>
          <p className="text-3xl font-bold text-gray-900 tracking-tight">
            {value}
          </p>
        </div>
        <div
          className={`
            w-12 h-12 rounded-xl flex items-center justify-center
            ${variant === 'success'
              ? 'bg-gradient-to-br from-emerald-100 to-emerald-200 text-emerald-700'
              : 'bg-gradient-to-br from-indigo-100 to-purple-200 text-indigo-700'
            }
          `}
        >
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </motion.div>
  );
}
