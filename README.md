# Leasing Agent

## Setup

### Prerequisites

- Poetry (for backend)
- Node.js and npm (for frontend)
- PostgreSQL database

### Database Setup

1. **Configure environment**

   ```bash
   cp backend/.env.template backend/.env
   ```

   Set `DATABASE_URL` to your local PostgreSQL database in the `.env` file.

2. **Run migrations**

   ```bash
   cd backend
   poetry run alembic upgrade head
   ```

3. **Seed database with dummy data**
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
