# Installation guide

## 1. Clone / open the project

Use the existing `cn` folder as the project root.

```powershell
cd C:\Users\deepa\cn
```

## 2. Verify tools

```powershell
python --version
node --version
npm --version
docker --version
wsl --status
```

From WSL (for ContainerLab later):

```bash
containerlab version
```

If ContainerLab is missing, install it inside Ubuntu WSL following the official ContainerLab docs. Do not install system packages from this project without approval.

## 3. Environment file

```powershell
Copy-Item .env.example .env
```

Adjust ports only if needed.

## 4. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload --port 8000
```

## 5. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## 6. Environment check script

Git Bash or WSL:

```bash
chmod +x scripts/*.sh
./scripts/check_environment.sh
```

## 7. Lab deploy (deferred)

Only after ContainerLab is installed in WSL and Docker is running:

```bash
./scripts/deploy_lab.sh
./scripts/destroy_lab.sh
```

Initialization of this repository intentionally does **not** deploy the lab.
