# ACEest Gym Fitness — DevOps Assignment (BITS WILP)

## Application
Python/Tkinter gym client management system with SQLite, progress tracking, and charts.

## Tech Stack
- **App**: Python 3, Tkinter, SQLite, Matplotlib
- **CI/CD**: Jenkins Pipeline
- **Version Control**: Git
- **Deployment Target**: BITS VM Lab (Linux)

## Version History (Git Tags)
| Tag    | File              | Features Added                          |
|--------|-------------------|-----------------------------------------|
| v1.0   | Aceestver-1.0.py  | Basic program display                   |
| v1.1   | Aceestver-1.1.py  | Calorie factor, styles                  |
| v2.0   | Aceestver-2.1.2.py| SQLite DB, save/load client             |
| v2.1   | Aceestver-2.2.1.py| Progress chart (matplotlib)             |
| v2.2   | Aceestver-2.2.4.py| Height, target weight, workout logging  |
| v3.0   | Aceestver-3.0.1.py| Full workout + metrics + BMI (STABLE)   |
| v3.1   | Aceestver-3.1.2.py| Login, PDF export, AI program generator |
| v3.2   | Aceestver-3.2.4.py| Membership billing, embedded charts     |

## Jenkins Pipeline Stages
1. **Checkout** — pulls code from Git
2. **Setup Python Environment** — creates venv, installs deps
3. **Run Tests** — pytest; auto-rollback on failure
4. **Package** — tars the release with git commit hash
5. **Deploy to BITS VM** — SCP + SSH deploy; auto-rollback on failure
6. **Smoke Test** — validates syntax on VM; auto-rollback on failure

## Rollback Strategy
- `deploy.sh` saves the current symlink as `previous` before switching
- `rollback.sh` flips `current` symlink back to `previous`
- Jenkins calls `rollback.sh` automatically in `post { failure }` blocks
- Last 5 releases are kept on disk for manual rollback if needed

## Setup Instructions

### 1. On your local machine
```bash
git init
git add .
git commit -m "Initial commit - v1.0"
git tag v1.0

# Add each version as a commit + tag
git add app.py
git commit -m "feat: add SQLite persistence - v2.0"
git tag v2.0
# ... repeat for each version
```

### 2. Push to Git server (GitHub / GitLab / Gitea on BITS VM)
```bash
git remote add origin <your-git-repo-url>
git push -u origin main --tags
```

### 3. On the BITS VM — Install Jenkins
```bash
sudo apt update
sudo apt install -y openjdk-17-jdk
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt update && sudo apt install -y jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
# Access Jenkins at http://<VM-IP>:8080
```

### 4. On the BITS VM — Install Python deps
```bash
sudo apt install -y python3 python3-pip python3-venv python3-tk
sudo mkdir -p /opt/aceest-gym
sudo chown jenkins:jenkins /opt/aceest-gym
```

### 5. In Jenkins UI
1. New Item → Pipeline
2. Pipeline → "Pipeline script from SCM" → Git → your repo URL
3. Add credentials:
   - `BITS_VM_HOST` — VM IP address (Secret Text)
   - `BITS_VM_USER` — SSH username (Secret Text)
   - `BITS_VM_SSH_KEY` — SSH private key (SSH Username with private key)
4. Save → Build Now

### 6. Run the app on VM (after deploy)
```bash
cd /opt/aceest-gym/current
/opt/aceest-gym/venv/bin/python app.py
# For headless VM, use X11 forwarding:
# ssh -X user@vm-ip
# then run the above
```

## Simulating a Failure + Rollback (for demo)
```bash
# On your local machine, introduce a syntax error
echo "this is broken" >> app.py
git add app.py
git commit -m "bad deploy - will trigger rollback"
git push
# Jenkins will: run tests → fail → call rollback.sh → restore previous version
```
