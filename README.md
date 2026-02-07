# online-cinema-fast-api
An online cinema is a digital platform that allows users to select, watch, and purchase access to movies and other video materials via the internet.

# 🎬 Online Cinema API


## Fast start for developers

### 1. Requirements
Make sure that you have:
* **Python 3.12**
* **Docker & Docker Compose**
* **Poetry 2+** (`pip install poetry`)

### 2. Environment settings
Clone repo:
```bash
  git clone <url-repo>
  cd online-cinema-fast-api
```

### 3. Poetry virtual venv settings
```bash
  poetry config virtualenvs.in-project true
  poetry install
```

### 4. Docker + DB

```bash
  docker-compose up -d --build
  docker exec -it cinema_app alembic upgrade head
  docker exec -it cinema_app alembic revision --autogenerate -m "description" # after changes in models
  docker exec -it cinema_app alembic current # check DB status after migration
```

## Testing

The project uses **pytest** for automated testing. To ensure a clean environment, all tests automatically use an isolated **SQLite in-memory database**, so no extra database configuration is required for running tests.

### Local Execution
Ensure that all dependencies are installed via Poetry:
```bash
poetry install
```

Run all tests:
```bash
poetry run pytest
```

Run tests with a detailed verbose report:
```bash
poetry run pytest -v
```

### Docker Execution
If you are running the application using Docker Compose, use the following command to run tests inside the container:
```bash
docker-compose exec app poetry run pytest
```

### Code Quality (Linting & Formatting)
Before creating a Pull Request, please ensure your code adheres to the project's style guide using **Ruff**:

```bash
# Check for errors and auto-fix simple issues
poetry run ruff check . --fix

# Format the code according to project rules
poetry run ruff format .
```

### Before commit!!!
```bash
  python -m poetry run ruff check .
  python -m poetry run ruff format .
````

```bash
  docker-compose -f docker-compose-tests.yml up --build
````

The API will then be available at: http://localhost:8000
Swagger documentation: http://localhost:8000/docs

### **Team Development and Workflow**
Git Rules:
Branches: Create your branches from develop with the `feature/task-name prefix`.

Pull Requests: **Only to the develop branch**.

A minimum of 2 approvals from colleagues is required.

CI automatically checks the code with the Ruff linter and tests

Useful commands:
```bash
  poetry run ruff check .
```
-check the code with a linter.

```bash
  poetry run rough format .
```
— automatically format the code.

```bash
  docker-compose logs -f
```
— View database logs.

###  **Project structure**

src/auth — Authorization (Dev 1)

src/movies — Directory (Dev 2)

src/interactions — Feedback/Likes (Dev 3)

src/orders — Cart/Orders (Dev 4)

src/payments — Payments/Stripe (Dev 5)

src/core — Configuration and DB.

### **Technological stack (Tech Stack)**

**Based on the TK requirements, we will need the following set of tools:**

**Framework**: FastAPI (the basis of the project).

**Database**: PostgreSQL (via psycopg2-binary or asynchronous asyncpg).

**ORM**: SQLAlchemy 2.0 (asynchronous mode).

**Migrations**: Alembic.

**Task Queue**: Celery + Redis (for removing tokens and sending email)

**Authentication**: JWT (python-jose and passlib libraries).

**Payments**: Stripe SDK.

**Object Storage**: MinIO/S3 (for avatars).

**Validation**: Pydantic v2 (built into FastAPI).

**Testing**: Pytest + HTTPX
