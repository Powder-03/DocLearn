import { Link } from 'react-router-dom'
import { Plus, BookOpen, TrendingUp } from 'lucide-react'
import { useSessions, useDeleteSession } from '@/hooks'
import { Button, LoadingSpinner, Card, CardContent } from '@/components/ui'
import { SessionList } from '@/components/sessions'

export default function DashboardPage() {
  const { data, isLoading, error } = useSessions()
  const deleteSession = useDeleteSession()

  const handleDeleteSession = async (sessionId: string) => {
    if (window.confirm('Are you sure you want to delete this course?')) {
      await deleteSession.mutateAsync(sessionId)
    }
  }

  // Calculate stats
  const sessions = data?.sessions || []
  const activeCourses = sessions.filter((s) => s.status === 'IN_PROGRESS').length
  const completedCourses = sessions.filter((s) => s.status === 'COMPLETED').length
  const totalDaysLearned = sessions.reduce((acc, s) => acc + (s.current_day - 1), 0)

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load sessions. Please try again.</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Track your learning progress and continue your courses
          </p>
        </div>
        <Link to="/new">
          <Button leftIcon={<Plus className="w-4 h-4" />}>
            New Course
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
              <BookOpen className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{activeCourses}</p>
              <p className="text-sm text-gray-500">Active Courses</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{completedCourses}</p>
              <p className="text-sm text-gray-500">Completed</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{totalDaysLearned}</p>
              <p className="text-sm text-gray-500">Days Learned</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sessions List */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Courses</h2>
        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <SessionList
            sessions={sessions}
            isLoading={false}
            onDelete={handleDeleteSession}
          />
        )}
      </div>

      {/* Empty state CTA */}
      {!isLoading && sessions.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center">
              <BookOpen className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Start Your Learning Journey
            </h3>
            <p className="text-gray-500 mb-6 max-w-sm mx-auto">
              Create your first course and let your AI tutor guide you through
              personalized lessons.
            </p>
            <Link to="/new">
              <Button leftIcon={<Plus className="w-4 h-4" />}>
                Create Your First Course
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
