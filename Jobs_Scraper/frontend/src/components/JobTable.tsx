import { useState, useMemo, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { Job, JobStatus } from '../types';
import { JobTableRow } from './JobTableRow';
import { TableSkeletonLoader } from './SkeletonLoader';
import { FilterBadge } from './FilterBadge';

interface JobTableProps {
  jobs: Job[];
  loading: boolean;
  selectedStatus: JobStatus;
  onStatusFilterChange: (status: JobStatus) => void;
  onJobClick: (job: Job) => void;
  onStatusChange: (jobId: string, status: JobStatus) => void;
  statusCounts: Record<string, number>;
}

const ITEMS_PER_PAGE = 50;

const statusFilters: { value: JobStatus; label: string }[] = [
  { value: 'All', label: 'All Jobs' },
  { value: 'Not Set', label: 'Not Set' },
  { value: 'Interested', label: 'Interested' },
  { value: 'Applied', label: 'Applied' },
  { value: 'Screening Call', label: 'Screening' },
  { value: 'Interviewing', label: 'Interviewing' },
  { value: 'Offer', label: 'Offer' },
  { value: 'Rejected', label: 'Rejected' },
  { value: 'Not Interested', label: 'Not Interested' },
];

export function JobTable({
  jobs,
  loading,
  selectedStatus,
  onStatusFilterChange,
  onJobClick,
  onStatusChange,
  statusCounts,
}: JobTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  // Filter jobs based on search and status
  const filteredJobs = useMemo(() => {
    let filtered = jobs;

    // Filter by status
    if (selectedStatus !== 'All') {
      filtered = filtered.filter((job) => {
        const status = job.app_status || 'Not Set';
        return status === selectedStatus;
      });
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (job) =>
          job.job_title.toLowerCase().includes(query) ||
          job.company_name.toLowerCase().includes(query) ||
          job.location_full.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [jobs, selectedStatus, searchQuery]);

  // Pagination
  const totalPages = Math.ceil(filteredJobs.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, filteredJobs.length);
  const paginatedJobs = filteredJobs.slice(startIndex, endIndex);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedStatus, searchQuery]);

  const handlePrevPage = () => {
    setCurrentPage((prev) => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(totalPages, prev + 1));
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header with search and filters */}
      <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-b from-gray-50 to-white">
        {/* Search bar */}
        <div className="relative mb-6">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title, company, or location..."
            className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all text-sm font-medium"
          />
        </div>

        {/* Filter badges */}
        <div className="flex flex-wrap gap-3">
          {statusFilters.map((filter) => (
            <FilterBadge
              key={filter.value}
              label={filter.label}
              count={filter.value === 'All' ? jobs.length : statusCounts[filter.value] || 0}
              isActive={selectedStatus === filter.value}
              onClick={() => onStatusFilterChange(filter.value)}
              status={filter.value}
            />
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        {loading ? (
          <div className="p-8">
            <TableSkeletonLoader />
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
              <tr>
                <th className="px-8 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                  Job Title
                </th>
                <th className="px-8 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                  Company
                </th>
                <th className="px-8 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-8 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                  Added Date
                </th>
                <th className="px-8 py-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedJobs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-8 py-16 text-center">
                    <div className="flex flex-col items-center">
                      <div className="text-6xl mb-4 opacity-40">📋</div>
                      <h3 className="text-xl font-bold text-gray-900 mb-2">No jobs found</h3>
                      <p className="text-gray-500 max-w-md mb-4">
                        {jobs.length === 0 
                          ? "No jobs available. The database might be empty or there was an error loading jobs."
                          : `No jobs match your filters. Showing ${jobs.length} total jobs.`
                        }
                      </p>
                      {jobs.length > 0 && (
                        <button
                          onClick={() => {
                            setSearchQuery('');
                            onStatusFilterChange('All');
                          }}
                          className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors text-sm font-semibold"
                        >
                          Clear Filters
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                paginatedJobs.map((job) => (
                  <JobTableRow
                    key={job._id}
                    job={job}
                    onStatusChange={onStatusChange}
                    onJobClick={onJobClick}
                  />
                ))
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination footer */}
      {!loading && filteredJobs.length > 0 && (
        <div className="px-8 py-4 border-t border-gray-200 bg-gradient-to-b from-gray-50 to-white flex items-center justify-between">
          <div className="text-sm font-medium text-gray-600">
            Showing {startIndex + 1}-{endIndex} of {filteredJobs.length} jobs
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrevPage}
              disabled={currentPage === 1}
              className="px-4 py-2 rounded-lg border-2 border-gray-200 font-semibold text-sm text-gray-700 hover:border-indigo-500 hover:text-indigo-600 hover:bg-indigo-50 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:border-gray-200 disabled:hover:text-gray-700 disabled:hover:bg-transparent flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <button
              onClick={handleNextPage}
              disabled={currentPage >= totalPages}
              className="px-4 py-2 rounded-lg border-2 border-gray-200 font-semibold text-sm text-gray-700 hover:border-indigo-500 hover:text-indigo-600 hover:bg-indigo-50 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:border-gray-200 disabled:hover:text-gray-700 disabled:hover:bg-transparent flex items-center gap-2"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
