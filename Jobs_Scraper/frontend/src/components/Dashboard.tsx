import { useState, useMemo, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Briefcase, Building2, RefreshCw, Download, FileText } from 'lucide-react';
import { Job, JobStatus } from '../types';
import { useJobs } from '../hooks/useJobs';
import { useStats } from '../hooks/useStats';
import { StatCard } from './StatCard';
import { JobTable } from './JobTable';
import { SlideOverModal } from './SlideOverModal';
import { FileUpload } from './FileUpload';
import { exportJobs } from '../services/api';
import { redirectToLogin } from '../config';

async function uploadMasterResume(file: File): Promise<void> {
  const formData = new FormData();
  formData.append('resume', file);
  
  const response = await fetch('/api/upload_master_resume', {
    method: 'POST',
    credentials: 'include', // Include cookies for authentication
    body: formData,
  });
  
  if (!response.ok) {
    if (response.status === 401 || response.status === 302) {
      redirectToLogin();
      return; // Stop execution
    }
    throw new Error(`HTTP ${response.status}`);
  }
  
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.error || 'Upload failed');
  }
}

export function Dashboard() {
  const { jobs, loading: jobsLoading, refetch: refetchJobs } = useJobs();
  const { stats, loading: statsLoading, refetch: refetchStats } = useStats();
  const [selectedStatus, setSelectedStatus] = useState<JobStatus>('All');
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isSlideOverOpen, setIsSlideOverOpen] = useState(false);
  const [isResumeModalOpen, setIsResumeModalOpen] = useState(false);

  // Calculate status counts from jobs
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    jobs.forEach((job) => {
      const status = job.app_status || 'Not Set';
      counts[status] = (counts[status] || 0) + 1;
    });
    // Ensure 'All' count is total jobs
    counts['All'] = jobs.length;
    return counts;
  }, [jobs]);
  
  // Debug: Log jobs count
  useEffect(() => {
    console.log('Jobs loaded:', jobs.length);
    if (jobs.length > 0) {
      console.log('First job sample:', jobs[0]);
    }
  }, [jobs]);

  const handleJobClick = (job: Job) => {
    setSelectedJob(job);
    setIsSlideOverOpen(true);
  };

  const handleStatusChange = (jobId: string, status: JobStatus) => {
    // Update local state optimistically
    const updatedJobs = jobs.map((job) =>
      job._id === jobId ? { ...job, app_status: status } : job
    );
    // Refetch to get updated data
    refetchJobs();
    refetchStats();
  };

  const handleRefresh = () => {
    refetchJobs();
    refetchStats();
  };

  const handleResumeUploaded = async () => {
    setIsResumeModalOpen(false);
    alert('Resume uploaded successfully!');
    // Optionally refresh data
  };

  const handleNotesSaved = () => {
    refetchJobs();
  };

  const handleResumeGenerated = () => {
    refetchJobs();
    refetchStats();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30 glass">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-1">Dashboard</h1>
              <p className="text-gray-500 text-sm">
                Track and manage your job applications in one place
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsResumeModalOpen(true)}
                className="px-4 py-2 rounded-xl border-2 border-gray-200 font-semibold text-sm text-gray-700 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50 transition-all flex items-center gap-2"
              >
                <FileText className="w-4 h-4" />
                Resume Settings
              </button>
              <button
                onClick={exportJobs}
                className="px-4 py-2 rounded-xl border-2 border-gray-200 font-semibold text-sm text-gray-700 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50 transition-all flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
              <button
                onClick={handleRefresh}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold text-sm hover:from-indigo-700 hover:to-purple-700 shadow-sm hover:shadow-md transition-all flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <StatCard
              label="Total Jobs"
              value={statsLoading ? '-' : stats?.total_jobs || 0}
              icon={Briefcase}
            />
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <StatCard
              label="Companies"
              value={statsLoading ? '-' : stats?.total_companies || 0}
              icon={Building2}
              variant="success"
            />
          </motion.div>
        </div>

        {/* Job table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <JobTable
            jobs={jobs}
            loading={jobsLoading}
            selectedStatus={selectedStatus}
            onStatusFilterChange={setSelectedStatus}
            onJobClick={handleJobClick}
            onStatusChange={handleStatusChange}
            onResumeGenerated={handleResumeGenerated}
            statusCounts={statusCounts}
          />
        </motion.div>
      </main>

      {/* Slide-over modal for job details */}
      <SlideOverModal
        isOpen={isSlideOverOpen}
        onClose={() => setIsSlideOverOpen(false)}
        job={selectedJob}
        onNotesSaved={handleNotesSaved}
      />

      {/* Resume upload modal */}
      {isResumeModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-8"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Resume Settings</h2>
              <button
                onClick={() => setIsResumeModalOpen(false)}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-500 hover:text-gray-900"
              >
                ×
              </button>
            </div>
            <FileUpload onUpload={uploadMasterResume} />
          </motion.div>
        </div>
      )}
    </div>
  );
}
