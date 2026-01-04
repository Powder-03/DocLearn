import api from '@/lib/api'
import type {
  Session,
  SessionListResponse,
  CreatePlanRequest,
  CreatePlanResponse,
  LessonPlanResponse,
  ProgressResponse,
  UpdateProgressRequest,
} from '@/types'

export const sessionService = {
  // Create a new learning session
  async createSession(data: CreatePlanRequest): Promise<CreatePlanResponse> {
    const response = await api.post<CreatePlanResponse>('/sessions', data)
    return response.data
  },

  // Get all sessions for the current user
  async getSessions(params?: {
    mode?: string
    status?: string
    limit?: number
    offset?: number
  }): Promise<SessionListResponse> {
    const response = await api.get<SessionListResponse>('/sessions', { params })
    return response.data
  },

  // Get a specific session
  async getSession(sessionId: string): Promise<Session> {
    const response = await api.get<Session>(`/sessions/${sessionId}`)
    return response.data
  },

  // Get lesson plan for a session
  async getLessonPlan(sessionId: string): Promise<LessonPlanResponse> {
    const response = await api.get<LessonPlanResponse>(`/sessions/${sessionId}/plan`)
    return response.data
  },

  // Get content for a specific day
  async getDayContent(sessionId: string, day: number): Promise<unknown> {
    const response = await api.get(`/sessions/${sessionId}/plan/day/${day}`)
    return response.data
  },

  // Update session progress
  async updateProgress(
    sessionId: string,
    data: UpdateProgressRequest
  ): Promise<ProgressResponse> {
    const response = await api.patch<ProgressResponse>(
      `/sessions/${sessionId}/progress`,
      data
    )
    return response.data
  },

  // Advance to next day
  async advanceDay(sessionId: string): Promise<ProgressResponse> {
    const response = await api.post<ProgressResponse>(
      `/sessions/${sessionId}/advance-day`
    )
    return response.data
  },

  // Go to a specific day
  async gotoDay(sessionId: string, day: number): Promise<ProgressResponse> {
    const response = await api.post<ProgressResponse>(
      `/sessions/${sessionId}/goto-day/${day}`
    )
    return response.data
  },

  // Delete a session
  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/sessions/${sessionId}`)
  },
}
