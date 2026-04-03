# ACEest Fitness & Gym — DevOps Assignment (BITS WILP)

## Overview
Flask-based gym client management REST API with a full DevOps pipeline:
Git → GitHub → GitHub Actions CI → Jenkins BUILD → Docker.

## Tech Stack
- **App**: Python 3.11, Flask, SQLite
- **Tests**: Pytest
- **Container**: Docker
- **CI**: GitHub Actions
- **BUILD**: Jenkins
- **VCS**: Git / GitHub

## Local Setup & Execution

```bash
# 1. Clone the repo
git clone https://github.com/2024tm93502-Viveka_M/aceest-gym.git
cd aceest-gym

# 2. Create virtual environment and install deps
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Run the app
python app.py
# App runs at http://localhost:5000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check + version |
| GET | `/programs` | List all fitness programs |
| POST | `/clients` | Save a client |
| GET | `/clients/<name>` | Get client details |
| POST | `/clients/<name>/progress` | Log weekly adherence |
| GET | `/clients/<name>/bmi` | Calculate BMI |

## Running Tests Manually

```bash
# Activate venv first
pytest tests/ -v
```

## Docker

```bash
# Build image
docker build -t aceest-gym .

# Run container
docker run -p 5000:5000 aceest-gym

# Run tests inside container
docker run --rm aceest-gym pytest tests/ -v
```

## GitHub Actions CI Pipeline

Triggered on every `push` and `pull_request` to `main`.

Stages:
1. **Lint** — `py_compile` checks for syntax errors
2. **Unit Tests** — pytest runs against the Flask app
3. **Docker Build** — builds the container image
4. **Container Tests** — pytest runs inside the built container

Pipeline file: `.github/workflows/main.yml`

## Jenkins BUILD Integration

Jenkins pulls the latest code from GitHub and performs:
1. **Checkout** — pulls from GitHub
2. **Lint** — syntax validation
3. **Docker Build** — builds the image tagged with `BUILD_NUMBER`
4. **Run Tests in Container** — pytest inside Docker
5. **Tag as Latest** — marks the image as `aceest-gym:latest`

Pipeline file: `Jenkinsfile`

### Jenkins Setup on BITS VM
1. Open Jenkins at `http://<bits-vm-ip>:8080`
2. New Item → Pipeline → name it `aceest-gym`
3. Pipeline → Pipeline script from SCM → Git
4. Repository URL → your GitHub repo URL
5. Branch → `*/main` | Script Path → `Jenkinsfile`
6. Save → Build Now

## Version History

| Tag | Description |
|-----|-------------|
| v1.0 | Initial Flask app with SQLite |
| v2.0 | Added progress tracking endpoints |
| v3.0 | Full BMI, metrics, workout logging (STABLE) |
