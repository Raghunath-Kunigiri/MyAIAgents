import { useState } from 'react';
import { motion } from 'framer-motion';
import { ExternalLink } from 'lucide-react';
import { Job, JobStatus } from '../types';
import { StatusDropdown } from './StatusDropdown';
import { updateJobStatus } from '../services/api';

interface JobTableRowProps {
  job: Job;
  onStatusChange: (jobId: string, status: JobStatus) => void;
  onJobClick: (job: Job) => void;
}

export function JobTableRow({ job, onStatusChange, onJobClick }: JobTableRowProps) {
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

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
        </div>
      </td>
    </motion.tr>
  );
}
