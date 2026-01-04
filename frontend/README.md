# DocLearn Frontend

React TypeScript frontend for the DocLearn AI-powered learning platform.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and builds
- **TailwindCSS** for styling
- **React Query** for data fetching and caching
- **React Router** for navigation
- **Clerk** for authentication
- **Axios** for API calls

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env
```

### Configuration

Edit `.env` and add your Clerk publishable key:

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
```

### Development

```bash
# Start development server
npm run dev
```

The app will be available at http://localhost:3000

The Vite dev server proxies `/api` requests to the backend at `http://localhost:8080`.

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── components/       # Reusable UI components
│   ├── chat/        # Chat-related components
│   ├── layout/      # Layout components (Header, etc.)
│   ├── sessions/    # Session list and cards
│   └── ui/          # Generic UI components (Button, Input, etc.)
├── hooks/           # Custom React hooks
├── lib/             # Utilities and API client
├── pages/           # Page components
├── services/        # API service functions
└── types/           # TypeScript type definitions
```

## Features

- **Authentication**: Sign in/up with Clerk
- **Dashboard**: View and manage learning sessions
- **Create Course**: Generate AI-powered learning plans
- **Chat Interface**: Interactive chat with AI tutor
- **Streaming Responses**: Real-time SSE streaming for AI responses
- **Progress Tracking**: Track learning progress across days/topics

## Deployment

The frontend is designed to be deployed alongside the backend using Cloud Build. See the root `cloudbuild.yaml` for the combined deployment configuration.

### Standalone Deployment

If deploying separately, build the Docker image:

```bash
docker build -t doclearn-frontend \
  --build-arg VITE_CLERK_PUBLISHABLE_KEY=your_key \
  --build-arg VITE_API_URL=https://your-api-url.com/api/v1 \
  .
```
