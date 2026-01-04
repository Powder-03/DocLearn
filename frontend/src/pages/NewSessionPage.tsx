import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Clock, Calendar, ArrowLeft, Loader2 } from 'lucide-react'
import { useCreateSession } from '@/hooks'
import { Button, Input, Card, CardContent, CardHeader } from '@/components/ui'

export default function NewSessionPage() {
  const navigate = useNavigate()
  const createSession = useCreateSession()

  const [formData, setFormData] = useState({
    topic: '',
    total_days: 7,
    time_per_day: '1 hour',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const timeOptions = [
    '15 minutes',
    '30 minutes',
    '45 minutes',
    '1 hour',
    '1.5 hours',
    '2 hours',
    '3 hours',
  ]

  const dayPresets = [
    { label: '1 Week', value: 7 },
    { label: '2 Weeks', value: 14 },
    { label: '1 Month', value: 30 },
    { label: '2 Months', value: 60 },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validate
    const newErrors: Record<string, string> = {}
    if (!formData.topic.trim()) {
      newErrors.topic = 'Please enter a topic'
    } else if (formData.topic.length < 3) {
      newErrors.topic = 'Topic must be at least 3 characters'
    }
    if (formData.total_days < 1 || formData.total_days > 90) {
      newErrors.total_days = 'Days must be between 1 and 90'
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    try {
      const result = await createSession.mutateAsync(formData)
      navigate(`/session/${result.session_id}`)
    } catch (error) {
      console.error('Failed to create session:', error)
      setErrors({ submit: 'Failed to create course. Please try again.' })
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </button>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Create New Course
              </h1>
              <p className="text-gray-500 text-sm">
                Let AI create a personalized learning plan for you
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Topic */}
            <div>
              <Input
                label="What do you want to learn?"
                placeholder="e.g., Machine Learning Basics, Spanish Language, Web Development"
                value={formData.topic}
                onChange={(e) =>
                  setFormData({ ...formData, topic: e.target.value })
                }
                error={errors.topic}
                className="text-lg"
              />
              <p className="mt-2 text-sm text-gray-500">
                Be specific for better results. For example, "React.js for
                beginners" instead of just "Programming"
              </p>
            </div>

            {/* Duration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                <Calendar className="w-4 h-4 inline mr-2" />
                How many days?
              </label>
              <div className="flex flex-wrap gap-2 mb-3">
                {dayPresets.map((preset) => (
                  <button
                    key={preset.value}
                    type="button"
                    onClick={() =>
                      setFormData({ ...formData, total_days: preset.value })
                    }
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      formData.total_days === preset.value
                        ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                        : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
                    }`}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-3">
                <Input
                  type="number"
                  min={1}
                  max={90}
                  value={formData.total_days}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      total_days: parseInt(e.target.value) || 1,
                    })
                  }
                  error={errors.total_days}
                  className="w-24"
                />
                <span className="text-gray-600">days</span>
              </div>
            </div>

            {/* Time per day */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                <Clock className="w-4 h-4 inline mr-2" />
                Time commitment per day
              </label>
              <div className="flex flex-wrap gap-2">
                {timeOptions.map((time) => (
                  <button
                    key={time}
                    type="button"
                    onClick={() =>
                      setFormData({ ...formData, time_per_day: time })
                    }
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      formData.time_per_day === time
                        ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                        : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
                    }`}
                  >
                    {time}
                  </button>
                ))}
              </div>
            </div>

            {/* Error message */}
            {errors.submit && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {errors.submit}
              </div>
            )}

            {/* Submit */}
            <Button
              type="submit"
              size="lg"
              className="w-full"
              disabled={createSession.isPending}
            >
              {createSession.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  Creating your course...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Generate Learning Plan
                </>
              )}
            </Button>

            {createSession.isPending && (
              <p className="text-center text-sm text-gray-500">
                This may take a minute while AI creates your personalized
                curriculum...
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
