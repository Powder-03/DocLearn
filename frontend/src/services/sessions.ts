import { apiRequest } from './api';
import type {
  Session,
  SessionListResponse,
  CreatePlanRequest,
  CreatePlanResponse,
  LessonPlanResponse,
  ProgressResponse,
  UpdateProgressRequest,
  DayPlan,
  UploadBookResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1';

export const sessionService = {
  // Create a new learning session
  create: (data: CreatePlanRequest): Promise<CreatePlanResponse> => {
    return apiRequest<CreatePlanResponse>('/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Upload a book for RAG session (multipart form data)
  uploadBook: async (sessionId: string, file: File): Promise<UploadBookResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');
    const url = `${API_BASE_URL}/sessions/${sessionId}/upload-book`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        // Don't set Content-Type — browser sets it with boundary for FormData
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail));
    }

    return response.json();
  },

  // List all sessions for the current user
  list: (params?: {
    mode?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<SessionListResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.mode) searchParams.set('mode', params.mode);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    
    const queryString = searchParams.toString();
    return apiRequest<SessionListResponse>(`/sessions${queryString ? `?${queryString}` : ''}`);
  },

  // Get session details
  get: (sessionId: string): Promise<Session> => {
    return apiRequest<Session>(`/sessions/${sessionId}`);
  },

  // Get lesson plan
  getPlan: (sessionId: string): Promise<LessonPlanResponse> => {
    return apiRequest<LessonPlanResponse>(`/sessions/${sessionId}/plan`);
  },

  // Get specific day content
  getDayContent: (sessionId: string, day: number): Promise<DayPlan> => {
    return apiRequest<DayPlan>(`/sessions/${sessionId}/plan/day/${day}`);
  },

  // Update progress
  updateProgress: (sessionId: string, data: UpdateProgressRequest): Promise<ProgressResponse> => {
    return apiRequest<ProgressResponse>(`/sessions/${sessionId}/progress`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  // Advance to next day
  advanceDay: (sessionId: string): Promise<ProgressResponse> => {
    return apiRequest<ProgressResponse>(`/sessions/${sessionId}/advance-day`, {
      method: 'POST',
    });
  },

  // Go to specific day
  gotoDay: (sessionId: string, day: number): Promise<ProgressResponse> => {
    return apiRequest<ProgressResponse>(`/sessions/${sessionId}/goto-day/${day}`, {
      method: 'POST',
    });
  },

  // Delete session
  delete: (sessionId: string): Promise<void> => {
    return apiRequest<void>(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },
};
