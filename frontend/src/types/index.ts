// Session types
export interface Session {
  session_id: string
  user_id: string
  topic: string
  total_days: number
  time_per_day: string
  current_day: number
  current_topic_index: number
  status: 'PLANNING' | 'READY' | 'IN_PROGRESS' | 'COMPLETED'
  mode: string
  lesson_plan?: LessonPlan
  created_at: string
  updated_at: string
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
}

export interface CreatePlanRequest {
  topic: string
  total_days: number
  time_per_day: string
}

export interface CreatePlanResponse {
  session_id: string
  status: string
  message: string
  lesson_plan?: LessonPlan
}

// Lesson plan types
export interface LessonPlan {
  overview: string
  days: DayPlan[]
}

export interface DayPlan {
  day: number
  title: string
  objectives: string[]
  topics: TopicPlan[]
  estimated_time: string
}

export interface TopicPlan {
  title: string
  description: string
  key_points: string[]
}

export interface LessonPlanResponse {
  session_id: string
  topic: string
  lesson_plan: LessonPlan
  current_day: number
  total_days: number
  progress_percentage: number
}

// Chat types
export interface ChatMessage {
  role: 'human' | 'assistant'
  content: string
  timestamp?: string
}

export interface ChatRequest {
  session_id: string
  message: string
}

export interface ChatResponse {
  session_id: string
  response: string
  current_day: number
  current_topic_index: number
  is_day_complete: boolean
  is_course_complete: boolean
}

export interface ChatHistoryResponse {
  session_id: string
  messages: ChatMessage[]
  total_messages: number
  current_day: number
  summaries: string[]
  total_summaries: number
}

export interface StartLessonRequest {
  session_id: string
  day?: number
}

export interface StartLessonResponse {
  session_id: string
  current_day: number
  day_title: string
  objectives: string[]
  welcome_message: string
}

// Progress types
export interface ProgressResponse {
  session_id: string
  current_day: number
  current_topic_index: number
  total_days: number
  is_complete: boolean
  progress_percentage: number
}

export interface UpdateProgressRequest {
  current_day?: number
  current_topic_index?: number
}

// SSE Event types
export interface SSETokenEvent {
  content: string
}

export interface SSEDoneEvent {
  current_day: number
  current_topic_index: number
  is_day_complete: boolean
  is_course_complete: boolean
}

export interface SSEErrorEvent {
  error: string
}
