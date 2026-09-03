# SafeDig — Production Deployment Guide

This guide details all production deployment methods for the **SafeDig AI Map QA & Validation Platform**.

---

## 1. Quick Comparison of Deployment Methods

| Method | Best For | Complexity | Pre-requisites |
|:---|:---|:---|:---|
| **Option 1: Docker Compose** *(Recommended)* | Production Linux VM, Cloud Instance (AWS/Azure/GCP) | Low (Single Command) | Docker & Docker Compose |
| **Option 2: Linux Bare-Metal / VM** | Ubuntu / Debian EC2 with Systemd & Nginx | Medium | Python 3.11, Nginx |
| **Option 3: Cloud PaaS (Render / Railway / GCP Cloud Run)** | Managed serverless container deployment | Low | Git repo + Dockerfile |
| **Option 4: Windows Host / On-Premise VM** | Corporate Windows Server / Workstation | Very Low | Python 3.11 |

---

## 2. Option 1: Docker & Docker Compose (Recommended)

This is the cleanest, most reproducible deployment. All dependencies (OpenCV, PyMuPDF, Shapely, fonts, and C libraries) are isolated inside the container.

### Step 1: Ensure Docker is Installed
Verify on your server:
```bash
docker --version
docker compose version
```

### Step 2: Build & Start Container
From the repository root (`d:/Safedig_AG` or `/opt/safedig`):
```bash
docker compose up -d --build
```

### Step 3: Verify Container Health
```bash
docker compose ps
docker compose logs -f
```

The container includes an automated health probe that checks `http://localhost:8000/api/v1/health` every 30 seconds.

### Step 4: Access Console
Navigate to:
```
http://<your-server-ip>:8000/
```

### Stopping & Updating
```bash
# Stop containers
docker compose down

# Update code and restart
git pull
docker compose up -d --build
```

---

## 3. Option 2: Linux Server Deployment (Ubuntu / Debian + Systemd + Nginx)

For dedicated Linux instances (e.g. AWS EC2 Ubuntu 22.04 / 24.04, Azure Linux VM, or DigitalOcean Droplet).

### Step 1: Install System Libraries
```bash
sudo apt update && sudo apt install -y \
    python3.11 python3.11-venv python3.11-dev \
    libgl1 libglib2.0-0 curl gcc nginx git
```

### Step 2: Set Up Repository & Virtual Environment
```bash
# Clone to /opt/safedig
sudo mkdir -p /opt/safedig
sudo chown -R $USER:$USER /opt/safedig
git clone <your-repo-url> /opt/safedig
cd /opt/safedig

# Create virtualenv and install dependencies
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run Database Migrations & Initial Verification
```bash
# Run automated tests to verify clean environment
pytest tests/ -v
```

### Step 4: Configure Systemd Service (Auto-Start on Boot)
Copy the provided unit file:
```bash
sudo cp safedig.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable safedig
sudo systemctl start safedig
sudo systemctl status safedig
```

### Step 5: Configure Nginx as Reverse Proxy
```bash
sudo cp nginx_safedig.conf /etc/nginx/sites-available/safedig.conf
sudo ln -s /etc/nginx/sites-available/safedig.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: Enable HTTPS with Let's Encrypt (Certbot)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d safedig.yourdomain.com
```

---

## 4. Option 3: Cloud PaaS Deployment (Render / Railway / GCP Cloud Run)

SafeDig includes a production `Dockerfile` that works out-of-the-box on container-native platforms:

### Deploying to Render:
1. Connect your GitHub/GitLab repository to **Render**.
2. Select **"New Web Service"**.
3. Choose **Docker** as the Runtime environment.
4. Set Instance Type: **Standard (at least 1GB-2GB RAM recommended for PDF rasterization)**.
5. Set Environment Variables:
   - `SAFEDIG_OUTPUT_DIR=/tmp/qa_output`
   - `SAFEDIG_ENGINE_VERSION=1.0.0`
6. Click **Deploy**.

---

## 5. Option 4: Windows Host / Windows Server Deployment

To run directly on Windows:

### Quick Run:
Double-click `run_production.bat` or run in PowerShell:
```powershell
.\run_production.bat
```
This launches Uvicorn on port 8000 with 4 worker processes.

### Running as a Persistent Windows Service (NSSM):
To make SafeDig auto-start with Windows and recover from crashes:
1. Download **NSSM** (Non-Sucking Service Manager) from `nssm.cc`.
2. Open Administrator Command Prompt:
   ```cmd
   nssm install SafeDigService "C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe" "-m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --workers 4"
   nssm set SafeDigService AppDirectory "d:\Safedig_AG"
   nssm set SafeDigService Description "SafeDig AI Map QA & Validation Console"
   nssm start SafeDigService
   ```

---

## 6. Environment Variables Reference

| Variable | Default Value | Description |
|:---|:---|:---|
| `SAFEDIG_HOST` | `0.0.0.0` | Bind IP address for web server |
| `SAFEDIG_PORT` | `8000` | Port for web server |
| `SAFEDIG_OUTPUT_DIR` | `qa_output` | Directory for job reports, crops & evidence packages |
| `SAFEDIG_SQLITE_URL` | `sqlite+aiosqlite:///safedig.db` | Async SQLAlchemy database URL |
| `SAFEDIG_ENGINE_VERSION`| `1.0.0` | Active detection engine version |
| `SAFEDIG_POLICY_VERSION`| `1.0.0` | Active 17 release gates policy version |
| `ANTHROPIC_API_KEY` | *(Optional)* | Key for Advisory Copilot LLM |
| `OPENAI_API_KEY` | *(Optional)* | Alternative key for Advisory Copilot |

---

## 7. Production Health & Monitoring Checks

After deploying, verify the system status using standard HTTP probes:

```bash
# Health probe (Liveness)
curl -f http://localhost:8000/api/v1/health

# Readiness & DB check
curl -f http://localhost:8000/api/v1/jobs

# Metrics probe
curl -f http://localhost:8000/api/v1/eval/latest
```
