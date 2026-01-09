import { useState } from 'react';
import { motion } from 'framer-motion';
import { ExternalLink, Download, RefreshCw, Sparkles } from 'lucide-react';
import { Job, JobStatus } from '../types';
import { StatusDropdown } from './StatusDropdown';
import { updateJobStatus, generateResume, downloadResume } from '../services/api';

interface JobTableRowProps {
  job: Job;
  onStatusChange: (jobId: string, status: JobStatus) => void;
  onJobClick: (job: Job) => void;
  onResumeGenerated: () => void;
}

export function JobTableRow({ job, onStatusChange, onJobClick, onResumeGenerated }: JobTableRowProps) {
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [isGeneratingResume, setIsGeneratingResume] = useState(false);

  const handleStatusChange = async (status: JobStatus) => {
    if (!status) return; // Don't update if no status selected
    setIsUpdatingStatus(true);
    try {
      const success = await updateJobStatus(job._id, status);
      if (success) {
        onStatusChange(job._id, status);
      } else {
        alert('Failed to update status. Please try again.');
      }
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Error updating status: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleGenerateResume = async () => {
    setIsGeneratingResume(true);
    try {
      const result = await generateResume(job._id);
      if (result.success) {
        alert('Resume generated successfully!');
        onResumeGenerated();
      } else {
        alert(`Error: ${result.error || 'Failed to generate resume'}`);
      }
    } catch (error) {
      console.error('Error generating resume:', error);
      alert('Error generating resume: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setIsGeneratingResume(false);
    }
  };


  return (
    <motion.tr
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="border-b border-gray-100 hover:bg-gradient-to-r hover:from-indigo-50/50 hover:to-transparent transition-colors group"
    >
      <td
        className="px-8 py-6 cursor-pointer"
        onClick={() => onJobClick(job)}
      >
        <div>
          <div className="font-semibold text-gray-900 text-[15px] mb-1 group-hover:text-indigo-600 transition-colors">
            {job.job_title}
          </div>
          <div className="text-sm text-gray-500">{job.location_full}</div>
        </div>
      </td>
      <td className="px-8 py-6">
        <div className="font-semibold text-gray-900 text-[15px]">{job.company_name}</div>
      </td>
      <td className="px-8 py-6">
        <StatusDropdown
          value={(job.app_status as JobStatus) || null}
          onChange={handleStatusChange}
          disabled={isUpdatingStatus}
        />
      </td>
      <td className="px-8 py-6">
        <div className="text-sm text-gray-500 font-medium">{job.timestamp_added}</div>
      </td>
      <td className="px-8 py-6">
        <div className="flex items-center justify-end gap-2">
          {job.job_url && (
            <a
              href={job.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg text-xs font-semibold border-2 border-gray-200 text-gray-700 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50 transition-all flex items-center gap-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              View
            </a>
          )}
          {job.resume_id ? (
            <>
              <button
                onClick={() => downloadResume(job.resume_id!)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:from-emerald-600 hover:to-emerald-700 shadow-sm hover:shadow-md transition-all flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                Download
              </button>
              <button
                onClick={handleGenerateResume}
                disabled={isGeneratingResume}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold border-2 border-gray-200 text-gray-700 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                title="Regenerate Resume"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingResume ? 'animate-spin' : ''}`} />
              </button>
            </>
          ) : (
            <button
              onClick={handleGenerateResume}
              disabled={isGeneratingResume}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:from-indigo-600 hover:to-purple-700 shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {isGeneratingResume ? 'Generating...' : 'Generate'}
            </button>
          )}
        </div>
      </td>
    </motion.tr>
  );
}
