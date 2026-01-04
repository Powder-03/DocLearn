import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionService } from '@/services'
import type { CreatePlanRequest } from '@/types'

export function useSessions(params?: {
  mode?: string
  status?: string
  limit?: number
  offset?: number
}) {
  return useQuery({
    queryKey: ['sessions', params],
    queryFn: () => sessionService.getSessions(params),
  })
}

export function useSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => sessionService.getSession(sessionId!),
    enabled: !!sessionId,
  })
}

export function useLessonPlan(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['lessonPlan', sessionId],
    queryFn: () => sessionService.getLessonPlan(sessionId!),
    enabled: !!sessionId,
  })
}

export function useCreateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreatePlanRequest) => sessionService.createSession(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
    },
  })
}

export function useDeleteSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => sessionService.deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
    },
  })
}

export function useAdvanceDay() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => sessionService.advanceDay(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
    },
  })
}

export function useGotoDay() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, day }: { sessionId: string; day: number }) =>
      sessionService.gotoDay(sessionId, day),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    },
  })
}
