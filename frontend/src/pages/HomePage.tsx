import { Link } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import { BookOpen, Sparkles, Brain, Target, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui'

export default function HomePage() {
  const { isSignedIn } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-primary-50">
      {/* Navigation */}
      <nav className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-accent-500">
              <BookOpen className="h-6 w-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
              DocLearn
            </span>
          </Link>
          <div className="flex items-center gap-4">
            {isSignedIn ? (
              <Link to="/dashboard">
                <Button>Go to Dashboard</Button>
              </Link>
            ) : (
              <>
                <Link to="/sign-in">
                  <Button variant="ghost">Sign In</Button>
                </Link>
                <Link to="/sign-up">
                  <Button>Get Started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 md:py-32">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-100 text-primary-700 text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            AI-Powered Personalized Learning
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Learn Anything with Your{' '}
            <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
              Personal AI Tutor
            </span>
          </h1>
          <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
            Create personalized learning paths, get adaptive lessons, and master
            any topic at your own pace with an AI tutor that understands you.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link to={isSignedIn ? '/new' : '/sign-up'}>
              <Button size="lg" className="px-8">
                Start Learning Free
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to={isSignedIn ? '/dashboard' : '/sign-in'}>
              <Button variant="secondary" size="lg">
                View Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Why DocLearn?
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Experience the future of learning with AI-powered personalization
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {/* Feature 1 */}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-14 h-14 rounded-xl bg-primary-100 flex items-center justify-center mb-6">
              <Brain className="w-7 h-7 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Adaptive Learning
            </h3>
            <p className="text-gray-600">
              AI that adapts to your learning style, pace, and level of
              understanding. Get personalized explanations and examples.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-14 h-14 rounded-xl bg-accent-100 flex items-center justify-center mb-6">
              <Target className="w-7 h-7 text-accent-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Structured Curriculum
            </h3>
            <p className="text-gray-600">
              AI-generated lesson plans tailored to your goals and schedule.
              Learn systematically with clear daily objectives.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-14 h-14 rounded-xl bg-green-100 flex items-center justify-center mb-6">
              <Sparkles className="w-7 h-7 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Interactive Chat
            </h3>
            <p className="text-gray-600">
              Ask questions anytime, get instant explanations, and have
              meaningful conversations about any topic you're learning.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center bg-gradient-to-r from-primary-600 to-accent-600 rounded-3xl p-12 text-white">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Transform Your Learning?
          </h2>
          <p className="text-lg text-white/90 mb-8 max-w-xl mx-auto">
            Join thousands of learners who are mastering new skills with their
            personal AI tutor.
          </p>
          <Link to={isSignedIn ? '/new' : '/sign-up'}>
            <Button
              size="lg"
              className="bg-white text-primary-600 hover:bg-gray-100 px-8"
            >
              Get Started Now
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary-500" />
            <span>DocLearn © 2026</span>
          </div>
          <p>Built with AI for better learning</p>
        </div>
      </footer>
    </div>
  )
}
