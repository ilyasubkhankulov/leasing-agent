## Running locally

## first, set up the database and run migrations

#### set up database

copy `backend/.env.template` to `backend/.env`

set DATABASE_URL to your local postgres database

#### run migrations

apply migration via `poetry run alembic upgrade head`

#### run seeds to populate database with dummy data

`poetry run python manage.py seed`

#### creating new migrations after changing models.py

`poetry run alembic revision --autogenerate -m 'MIGRATION_NAME'`

update the generated migration file and then apply migration via `poetry run alembic upgrade head`

#### create empty migration

`poetry run alembic revision -m "MIGRATION_NAME"`

apply migration via `poetry run alembic upgrade head`

## roll back migrations via `poetry run alembic downgrade base`

#### backend

prereq's: poetry

`cd backend`

`poetry install`

`poetry run fastapi dev app/main.py`

the backend should now be listening on 8000

#### frontend

`cd frontend`

`npm i`

`npm run dev`
