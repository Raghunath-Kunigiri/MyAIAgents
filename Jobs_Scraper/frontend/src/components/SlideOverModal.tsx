import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save } from 'lucide-react';
import { Job } from '../types';
import { updateJobNotes } from '../services/api';

interface SlideOverModalProps {
  isOpen: boolean;
  onClose: () => void;
  job: Job | null;
  onNotesSaved: () => void;
}

export function SlideOverModal({ isOpen, onClose, job, onNotesSaved }: SlideOverModalProps) {
  const [notes, setNotes] = useState(job?.notes || '');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (job) {
      setNotes(job.notes || '');
    }
  }, [job]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const handleSaveNotes = async () => {
    if (!job) return;
    setIsSaving(true);
    try {
      const success = await updateJobNotes(job._id, notes);
      if (success) {
        onNotesSaved();
        // Success feedback will be shown by parent component
      } else {
        alert('Failed to save notes. Please try again.');
      }
    } catch (error) {
      console.error('Error saving notes:', error);
      alert('Error saving notes: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setIsSaving(false);
    }
  };

  if (!job) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />
          
          {/* Slide-over panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-2xl bg-white shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-b from-gray-50 to-white flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">{job.job_title}</h2>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-500 hover:text-gray-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-8 py-6">
              {/* Meta information */}
              <div className="flex gap-8 mb-8 flex-wrap">
                <div>
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                    Company
                  </div>
                  <div className="text-lg font-semibold text-gray-900">{job.company_name}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                    Location
                  </div>
                  <div className="text-lg font-semibold text-gray-900">{job.location_full}</div>
                </div>
              </div>

              {/* Notes section */}
              <div className="mb-8">
                <label className="block text-sm font-semibold text-gray-900 mb-3">
                  Application Notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add private notes about this job (e.g. contact person, interview questions...)"
                  className="w-full min-h-[120px] px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all resize-y text-sm"
                />
                <button
                  onClick={handleSaveNotes}
                  disabled={isSaving}
                  className="mt-4 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold text-sm hover:from-indigo-700 hover:to-purple-700 shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Saving...' : 'Save Notes'}
                </button>
              </div>

              {/* Job Description */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Job Description</h3>
                <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {job.job_description || 'No description available.'}
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
