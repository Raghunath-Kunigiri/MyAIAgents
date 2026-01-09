export interface Job {
  _id: string;
  job_title: string;
  company_name: string;
  location_full: string;
  timestamp_added: string;
  job_url?: string;
  job_description: string;
  app_status: string | null;
  resume_id?: string;
  notes?: string;
}

export interface Stats {
  total_jobs: number;
  total_companies: number;
  duplicate_count: number;
  status_counts: Record<string, number>;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export type JobStatus = 
  | 'Interested'
  | 'Applied'
  | 'Screening Call'
  | 'Interviewing'
  | 'Offer'
  | 'Rejected'
  | 'Not Interested'
  | 'Not Set'
  | 'All';
