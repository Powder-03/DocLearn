import { useNavigate } from 'react-router-dom'
import { Calendar, Clock, BookOpen, Trash2 } from 'lucide-react'
import { Card, CardContent, Badge, ProgressBar, Button } from '@/components/ui'
import { formatTimeAgo, truncateText } from '@/lib/utils'
import type { Session } from '@/types'

interface SessionCardProps {
  session: Session
  onDelete?: (sessionId: string) => void
}

export default function SessionCard({ session, onDelete }: SessionCardProps) {
  const navigate = useNavigate()

  const getStatusBadge = () => {
    switch (session.status) {
      case 'COMPLETED':
        return <Badge variant="success">Completed</Badge>
      case 'IN_PROGRESS':
        return <Badge variant="info">In Progress</Badge>
      case 'READY':
        return <Badge variant="warning">Ready</Badge>
      case 'PLANNING':
        return <Badge variant="default">Planning</Badge>
      default:
        return <Badge variant="default">{session.status}</Badge>
    }
  }

  const progress = ((session.current_day - 1) / session.total_days) * 100

  const handleClick = () => {
    navigate(`/session/${session.session_id}`)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onDelete) {
      onDelete(session.session_id)
    }
  }

  return (
    <Card hover onClick={handleClick} className="group relative">
      <CardContent className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">
              {truncateText(session.topic, 50)}
            </h3>
            <p className="text-sm text-gray-500 mt-0.5">
              {formatTimeAgo(session.created_at)}
            </p>
          </div>
          {getStatusBadge()}
        </div>

        {/* Progress */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1.5">
            <span className="text-gray-600">
              Day {session.current_day} of {session.total_days}
            </span>
            <span className="text-gray-600">{Math.round(progress)}%</span>
          </div>
          <ProgressBar value={progress} size="sm" />
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-1.5">
            <Calendar className="h-4 w-4" />
            <span>{session.total_days} days</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="h-4 w-4" />
            <span>{session.time_per_day}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <BookOpen className="h-4 w-4" />
            <span>{session.mode}</span>
          </div>
        </div>

        {/* Delete button */}
        {onDelete && (
          <Button
            variant="ghost"
            size="sm"
            className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 hover:bg-red-50"
            onClick={handleDelete}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
