# DocLearn - AI-Powered Personalized Learning Platform

A production-ready AI microservice that provides personalized curriculum generation and interactive tutoring using Google Gemini models. Includes a React TypeScript frontend for a complete learning experience.

## Features

- **Dynamic Plan Generation**: Creates personalized, multi-day lesson plans based on topic, available time, and learning goals
- **Interactive Tutoring**: Socratic-method teaching with understanding checks using Gemini 2.5 Flash
- **Adaptive Streaming**: Burst mode for short responses (<100 tokens), streaming for longer explanations
- **Buffer-Based Memory**: 10-message buffer with automatic summarization for efficient context management
- **Progress Tracking**: Stateful learning across multiple sessions with day/topic progression
- **Modern React Frontend**: TypeScript, TailwindCSS, and Clerk authentication

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│   FastAPI App   │────▶│    MongoDB      │
│  (TypeScript)   │     │                 │     │  (All Storage)  │
│                 │     │  - Sessions     │     │                 │
│  - Clerk Auth   │     │  - Chat         │     └─────────────────┘
│  - React Query  │     │  - Health       │
│  - TailwindCSS  │     └────────┬────────┘
└─────────────────┘              │
                                 ▼
                        ┌─────────────────┐
                        │  Google Gemini  │
                        │  - 2.5 Pro      │ ◀── Planning
                        │  - 2.5 Flash    │ ◀── Tutoring
                        └─────────────────┘
```

## Project Structure

```
doclearn/
├── app/                      # Backend (FastAPI)
│   ├── core/                 # Configuration, prompts, LLM factory
│   ├── services/             # Business logic services
│   ├── graphs/               # LangGraph state machines
│   ├── api/routes/           # API endpoints
│   └── main.py               # FastAPI application
├── frontend/                 # Frontend (React TypeScript)
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API service functions
│   │   └── types/            # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── Dockerfile                # Backend only
├── Dockerfile.combined       # Frontend + Backend (production)
├── docker-compose.yml        # Local development
├── cloudbuild.yaml           # Google Cloud Build
└── README.md
```

## Running the Application

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Google Cloud API Key (for Gemini)
- Clerk account (for authentication)

### Local Development

#### Backend Only

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Google API key, MongoDB URL, and Clerk credentials
   ```

3. **Start MongoDB with Docker:**
   ```bash
   docker-compose up -d mongodb
   ```

4. **Run the backend:**
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```

#### Frontend Only

1. **Navigate to frontend:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Add your Clerk publishable key
   ```

3. **Run the frontend:**
   ```bash
   npm run dev
   ```

   Frontend: http://localhost:3000
   Backend API: http://localhost:8080

### Using Docker Compose (Full Stack)

```bash
# Create .env file with all required variables
cat > .env << EOF
GOOGLE_API_KEY=your_gemini_api_key
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_JWKS_URL=https://your-clerk.clerk.accounts.dev/.well-known/jwks.json
CLERK_ISSUER=https://your-clerk.clerk.accounts.dev
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key
EOF

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Mongo Express: http://localhost:8081

## API Endpoints

### Sessions
- `POST /api/v1/sessions` - Create a new learning session
- `GET /api/v1/sessions` - List user sessions
- `GET /api/v1/sessions/{id}` - Get session details
- `GET /api/v1/sessions/{id}/plan` - Get lesson plan
- `PATCH /api/v1/sessions/{id}/progress` - Update progress
- `DELETE /api/v1/sessions/{id}` - Delete session

### Chat
- `POST /api/v1/chat` - Send message (auto-detects streaming need)
- `POST /api/v1/chat/stream` - SSE streaming endpoint
- `POST /api/v1/chat/start-lesson` - Start/resume a lesson
- `GET /api/v1/chat/{session_id}/history` - Get chat history with summaries

### Health
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe (MongoDB + Gemini)

### Test Endpoints
- `GET /test/ping` - Simple ping (no dependencies)
- `GET /test/mongodb/status` - MongoDB connection check
- `POST /test/mongodb` - MongoDB write/read test
- `GET /test/gemini/status` - Gemini API configuration check
- `POST /test/gemini` - Gemini API call test

## Memory Buffer System

The application uses a 10-message buffer for efficient context management:

1. **Buffer Phase**: Messages are stored in MongoDB as they're exchanged
2. **Threshold**: When buffer reaches 10 messages, summarization triggers
3. **Summarization**: Gemini Flash summarizes the conversation
4. **Storage**: Summary is stored, buffer is cleared
5. **Context**: LLM receives summaries + recent buffer for full context

```
Buffer: [msg1, msg2, ..., msg10] → Summarize → [Summary 1]
Buffer: [msg11, msg12, ..., msg20] → Summarize → [Summary 1, Summary 2]
...
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | - | Google AI API key (required) |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection URL |
| `MONGODB_DB_NAME` | `doclearn` | MongoDB database name |
| `PLANNING_MODEL` | `gemini-2.5-pro` | Model for curriculum generation |
| `TUTORING_MODEL` | `gemini-2.5-flash` | Model for interactive tutoring |
| `STREAMING_TOKEN_THRESHOLD` | `100` | Tokens threshold for streaming |
| `MEMORY_BUFFER_SIZE` | `10` | Messages before summarization |

## Deployment

### Google Cloud Run (Combined Frontend + Backend)

The recommended deployment uses `Dockerfile.combined` to build and deploy both frontend and backend as a single container.

1. **Enable required APIs:**
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   ```

2. **Create secrets in Secret Manager:**
   ```bash
   # MongoDB connection string (e.g., MongoDB Atlas)
   echo -n "mongodb+srv://..." | gcloud secrets create doclearn-mongo-url --data-file=-
   
   # Google Gemini API key
   echo -n "your-gemini-key" | gcloud secrets create doclearn-gemini-key --data-file=-
   
   # Clerk secrets
   echo -n "sk_test_..." | gcloud secrets create doclearn-clerk-secret --data-file=-
   echo -n "https://your-clerk.clerk.accounts.dev/.well-known/jwks.json" | gcloud secrets create doclearn-clerk-jwks-url --data-file=-
   echo -n "https://your-clerk.clerk.accounts.dev" | gcloud secrets create doclearn-clerk-issuer --data-file=-
   ```

3. **Deploy using Cloud Build:**
   ```bash
   gcloud builds submit \
     --config cloudbuild.yaml \
     --substitutions=_CLERK_PUBLISHABLE_KEY="pk_test_your_key" \
     .
   ```

   Or set up a Cloud Build trigger connected to your repository.

The deployment will:
- Build the frontend with Vite
- Build the backend Python application
- Combine both into a single container with nginx + supervisord
- Deploy to Cloud Run with secrets mounted as environment variables

## MongoDB Collections

The application uses the following MongoDB collections:

- **learning_sessions**: Session documents with lesson plans and progress
- **chat_messages**: Chat message buffer with timestamps
- **chat_summaries**: Summarized conversation history
- **test_collection**: Temporary collection for diagnostic tests

## License

MIT
