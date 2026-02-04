# online-cinema-fast-api
An online cinema is a digital platform that allows users to select, watch, and purchase access to movies and other video materials via the internet.

# 🎬 Online Cinema API


## Fast start for developers

### 1. Requirements
Make sure that you have:
* **Python 3.12**
* **Docker & Docker Compose**
* **Poetry** (`pip install poetry`)

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
This will raise:

PostgreSQL on port 5432

Redis on port 6379

### 4. Docker

```bash
docker-compose up -d
```

### 5. Run app

```bash
poetry run uvicorn src.main:app --reload
```

The API will then be available at: http://127.0.0.1:8000 
Swagger documentation: http://127.0.0.1:8000/docs

### **Team Development and Workflow**
Git Rules:
Branches: Create your branches from develop with the `feature/task-name prefix`.

Pull Requests: **Only to the develop branch**.

A minimum of 2 approvals from colleagues is required.

CI automatically checks the code with the Ruff linter.

Useful commands:
```bash
poetry run ruff check
```
-check the code with a linter.

```bash
poetry run rough format.
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