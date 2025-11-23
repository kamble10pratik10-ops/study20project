# LearnConnect - Collaborative Learning Platform

## Overview

LearnConnect is a modern collaborative learning platform that connects learners through educational resource discovery and topic-based communities. The application enables users to search for YouTube videos and articles, create and join study groups, and participate in community-driven learning through a doubts/questions section.

The platform features a React-based SPA frontend with a FastAPI Python backend, JWT authentication, and SQLite database for data persistence. The project is structured as a full-stack application with separate client and server directories, built on a Fusion Starter template that includes Express (though the primary backend is FastAPI).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack:**
- React 18 with TypeScript for type safety
- Vite as the build tool and development server
- React Router v6 in SPA mode for client-side routing
- TailwindCSS 3 with custom theming for styling
- Radix UI components for accessible UI primitives
- React Query (TanStack Query) for server state management

**Routing System:**
- Routes are centrally defined in `client/App.tsx` using React Router's `BrowserRouter`
- Page components live in `client/pages/` (Index, Login, Signup, Dashboard, Search, Groups, GroupDetail, Doubts, NotFound)
- Layout wrapper provides consistent header/footer across authenticated and public routes
- Authentication state managed via localStorage tokens

**Component Architecture:**
- Shared layout components in `client/components/layout/` (Header, Layout)
- Pre-built UI component library in `client/components/ui/` using Radix UI primitives
- Theme system supports dark/light modes via CSS variables and localStorage persistence
- Mobile-responsive design using TailwindCSS breakpoints

### Backend Architecture

**Technology Stack:**
- FastAPI as the primary web framework (Python)
- SQLAlchemy ORM for database operations
- SQLite as the default database (upgradeable to PostgreSQL)
- Pydantic for request/response validation and settings management
- JWT tokens (python-jose) for stateless authentication
- Passlib with bcrypt for password hashing

**API Structure:**
- Modular route organization in `backend/api/` directory:
  - `auth.py` - User signup/login with JWT token generation
  - `dashboard.py` - User dashboard with recent searches, joined groups, recommended topics
  - `groups.py` - CRUD operations for study groups
  - `doubts.py` - Question/answer system for community learning
  - `search.py` - YouTube and article search integration
- Dependency injection pattern for database sessions and user authentication
- CORS middleware configured for local development

**Database Schema:**
- Users table with authentication credentials and profile information
- Topics table for subject categorization
- Groups table with many-to-many relationships to users (members)
- Doubts table for community questions linked to topics
- SearchHistory table tracking user search queries
- GroupResources table for sharing learning materials within groups
- Association tables (`group_members`, `user_interests`) for many-to-many relationships

**Authentication Flow:**
- JWT-based stateless authentication using Bearer tokens
- Password hashing with bcrypt (via Passlib)
- Token expiration configurable via environment settings (default 30 minutes)
- HTTPBearer security scheme for protected endpoints
- Current user extracted from token payload and validated against database

### Data Storage

**SQLite Database:**
- Default development database (`learnconnect.db`)
- Synchronous SQLAlchemy engine with session management
- Database initialization creates all tables on startup
- Default test user created automatically (abc@abc.com / abc123)
- Schema supports future migration to PostgreSQL without code changes

**State Management:**
- Client-side: localStorage for JWT tokens and user info
- Server-side: SQLAlchemy sessions with dependency injection pattern
- No global state management library (using React Query for server state)

### External Dependencies

**Third-Party APIs:**
- YouTube Data API v3 for video search (requires `YOUTUBE_API_KEY`)
- Bing Search API for article discovery (requires `BING_SEARCH_API_KEY`)
- Fallback placeholder data when API keys not configured

**Environment Configuration:**
- Settings managed via Pydantic BaseSettings from `.env` file
- Configuration includes database URL, JWT secrets, API keys, CORS origins
- Cached settings using `@lru_cache` for performance

**Development Tools:**
- Vite dev server on port 5000 with HMR (configured for 0.0.0.0 for Replit)
- FastAPI runs independently on port 8000 (backend API)
- Express server included but optional - FastAPI is the primary backend
- PNPM as the preferred package manager for Node dependencies

**Replit Environment Configuration:**
- Frontend: Configured on port 5000 with host 0.0.0.0 to work with Replit's proxy
- Backend: Running on port 8000 with localhost binding
- CORS: Uses `allow_origin_regex` pattern to match Replit domains (*.replit.dev, *.repl.co)
- Dependencies: Python 3.12 with bcrypt 4.1.2 for password hashing
- Workflows: 
  - "Frontend" workflow runs `npm run dev` on port 5000 (webview)
  - "Backend API" workflow runs `python main.py` on port 8000 (console)
- Deployment: Configured for autoscale deployment with npm build and start

**Production Considerations:**
- Client build outputs to `dist/spa/` 
- Server build outputs to `dist/server/`
- Express production server can serve the SPA build
- FastAPI runs as separate service (not integrated with Express in production)
- CORS configuration needs update for production domains
- JWT secret key must be changed from default
- Database should be migrated to PostgreSQL for production use

**Key Architectural Decisions:**

1. **Dual Backend Setup**: The project includes both Express (from the Fusion Starter template) and FastAPI backends. FastAPI is the active backend handling all API routes, while Express serves primarily as a potential production server for serving the built SPA.

2. **Stateless Authentication**: JWT tokens chosen over session-based auth for scalability and stateless API design, enabling easier horizontal scaling.

3. **SPA Architecture**: React Router in SPA mode provides client-side routing without server roundtrips, improving perceived performance and user experience.

4. **SQLite for Development**: Lightweight database choice for easy setup, with clear migration path to PostgreSQL for production without application code changes.

5. **Modular API Routes**: Backend routes organized by feature domain (auth, groups, doubts, etc.) for maintainability and clear separation of concerns.

6. **Component Library Approach**: Pre-built Radix UI components provide accessible, customizable primitives while maintaining consistent design system through TailwindCSS theming.