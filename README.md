# Leasing Agent

## Setup

### Prerequisites

- Poetry (for backend)
- Node.js and npm (for frontend)
- PostgreSQL database

### Environment Configuration

**1. Backend Environment Setup**

Copy the environment template and configure your settings:

```bash
cp backend/.env.template backend/.env
```

Edit `backend/.env` and set the following required variables:

- `DATABASE_URL` - PostgreSQL connection string (e.g., `postgresql://user:password@localhost/leasing_agent`)
- `FRONTEND_URL` - Frontend URL (e.g., `http://localhost:3000`)
- `OPENAI_API_KEY` - Your OpenAI API key

Optional variables:

- `ENVIRONMENT` - Environment name (default: `development`)
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `OPENAI_MODEL` - OpenAI model to use (default: `gpt-4.1`)

**2. Frontend Environment Setup**

Copy the environment template and configure your settings:

```bash
cp frontend/.env.template frontend/.env.local
```

Edit `frontend/.env.local` and set:

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL (e.g., `http://localhost:8000`)

### Database Setup

1. **Run migrations**

   ```bash
   cd backend
   poetry run alembic upgrade head
   ```

2. **Seed database with dummy data**
   ```bash
   poetry run python manage.py seed
   ```

## Running the Application

### Backend

```bash
cd backend
poetry install
poetry run fastapi dev app/main.py
```

The backend will be available at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Database Migrations

### Creating New Migrations

**After modifying models:**

```bash
poetry run alembic revision --autogenerate -m 'MIGRATION_NAME'
```

Review the generated migration file, then apply it:

```bash
poetry run alembic upgrade head
```

**Creating empty migration:**

```bash
poetry run alembic revision -m "MIGRATION_NAME"
poetry run alembic upgrade head
```

### Rolling Back Migrations

```bash
poetry run alembic downgrade base
```

## Run tests

```bash
cd backend
```

### Unit Tests

**Run all tests:**

```bash
make test
```
