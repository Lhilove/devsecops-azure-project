# 🔐 DevSecOps CI/CD Pipeline on Azure

A production-style DevSecOps project that demonstrates how to embed security into every stage of a software delivery pipeline — from code to cloud. Built with a deliberately vulnerable Flask app, secured through automated CI/CD gates, containerized with Docker, deployed to Azure Kubernetes Service (AKS), and provisioned with Terraform.

---

## 📌 Project Summary

This project follows the **shift-left security** approach — catching vulnerabilities early in the development lifecycle rather than after deployment. Security is not an afterthought; it is enforced as a hard gate at every stage of the pipeline.

> If the pipeline fails, nothing gets deployed.

---

## 🏗️ Architecture

```
Developer Push
      │
      ▼
GitHub Actions CI/CD Pipeline
      │
      ├── SAST (Bandit)           → Scans Python source code
      ├── SCA (Dependabot)        → Scans dependencies
      ├── Secrets Scan            → Detects hardcoded credentials
      └── Container Scan          → Docker Scout image analysis
                │
                ▼ (only if all checks pass)
         Azure Container Registry (ACR)
                │
                ▼
     Azure Kubernetes Service (AKS)
                │
                ▼
        Live Flask Application
        http://102.37.236.148
```

---

## 🧰 Tech Stack

| Category | Tool |
|---|---|
| Application | Python, Flask |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| SAST | Bandit |
| SCA | GitHub Dependabot |
| Container Scanning | Docker Scout |
| Secrets Detection | GitHub Secret Scanning |
| Cloud Platform | Microsoft Azure |
| Container Registry | Azure Container Registry (ACR) |
| Kubernetes | Azure Kubernetes Service (AKS) |
| Infrastructure as Code | Terraform |

---

## 📂 Project Structure

```
devsecops-azure-project/
│
├── app/
│   ├── app.py              # Flask application (secure version)
│   ├── init_db.py          # Database initialization
│   └── requirements.txt    # Python dependencies
│
├── .github/
│   └── workflows/
│       └── pipeline.yml    # GitHub Actions CI/CD pipeline
│
├── infra/
│   ├── main.tf             # Terraform - Azure resources
│   ├── variables.tf        # Terraform - input variables
│   └── outputs.tf          # Terraform - output values
│
├── k8s/
│   ├── deployment.yaml     # Kubernetes deployment manifest
│   └── service.yaml        # Kubernetes LoadBalancer service
│
├── Dockerfile              # Container build instructions
└── .gitignore
```

---

## 🐛 Phase 1: Intentionally Vulnerable Application

A Flask application was built with deliberate OWASP Top 10 vulnerabilities to serve as a realistic attack surface for security tooling.

### Endpoints & Vulnerabilities

| Endpoint | Vulnerability | OWASP Category |
|---|---|---|
| `POST /login` | SQL Injection | A03: Injection |
| `GET /user/<id>` | IDOR + Password Exposure | A01: Broken Access Control, A02: Cryptographic Failures |
| `GET /ping` | Command Injection | A03: Injection |
| `GET /config` | Hardcoded Secrets | A02: Cryptographic Failures |
| `GET /admin` | Broken Authentication | A01: Broken Access Control, A07: Auth Failures |
| `GET /debug` | Security Misconfiguration | A05: Security Misconfiguration |

---

## 🐳 Phase 2: Containerization

The application was containerized using Docker and pushed to both Docker Hub and Azure Container Registry.

```bash
docker build -t devsecops-app .
docker tag devsecops-app devsecopsakr123.azurecr.io/devsecops-app:latest
docker push devsecopsakr123.azurecr.io/devsecops-app:latest
```

---

## 🔄 Phase 3: CI/CD Security Pipeline

GitHub Actions pipeline triggers on every push to `main`. Each job must pass before the next runs.

```yaml
SAST (Bandit) → SCA (Dependabot) → Container Scan (Docker Scout)
```

### Pipeline Enforcement Rules
- Bandit fails on **MEDIUM and HIGH** severity findings
- Docker Scout fails on **CRITICAL and HIGH** CVEs
- Secrets scan blocks any detected credentials
- Deployment only proceeds if **all gates pass**

### Initial Pipeline Result (Vulnerable Code)
The pipeline **intentionally failed** when scanning the vulnerable application — proving the security gates work correctly.

### Final Pipeline Result (Remediated Code)
After remediation, the pipeline passed all stages with zero blocking findings.

---

## 🔧 Phase 4: Vulnerability Remediation

All identified vulnerabilities were fixed before deployment was permitted.

### SQL Injection → Parameterized Queries
```python
# Before (vulnerable)
query = f"SELECT * FROM users WHERE username='{username}'"

# After (secure)
query = "SELECT id, username FROM users WHERE username=? AND password=?"
cursor.execute(query, (username, password))
```

### Command Injection → Safe Subprocess + Input Validation
```python
# Before (vulnerable)
result = os.popen(f"ping -c 1 {ip}").read()

# After (secure)
if not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip):
    return jsonify({"error": "Invalid IP"}), 400

result = subprocess.run(["/bin/ping", "-c", "1", ip], capture_output=True, text=True)  # nosec B603
```

### Broken Access Control → Token-Based Auth
```python
# Before (vulnerable)
if role == "admin":   # user controls their own role
    return "Welcome admin!"

# After (secure)
token = request.headers.get("Authorization")
if token == os.getenv("ADMIN_TOKEN"):
    return "Welcome admin!"
return "Access denied", 403
```

### Sensitive Data Exposure → Remove Secrets from Responses
```python
# Before (vulnerable)
return jsonify({"db_password": "supersecret123", "api_key": "12345-SECRET-KEY"})

# After (secure)
return jsonify({"status": "OK"})
```

### Security Headers Added
```python
@app.after_request
def set_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## ☁️ Phase 5: Azure Deployment (AKS)

The secure image was deployed to Azure Kubernetes Service with secrets managed via Kubernetes Secrets — not hardcoded in manifests.

```bash
# Create Kubernetes secret
kubectl create secret generic app-secrets \
  --from-literal=ADMIN_TOKEN=<token> \
  --from-literal=USER_TOKEN=<token>

# Deploy
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Live Endpoints
| Endpoint | Expected Result |
|---|---|
| `GET /` | `Secure DevSecOps App Running` |
| `GET /admin` (no token) | `403 Access Denied` |
| `GET /admin` (valid token) | `Welcome admin!` |
| `GET /user/1` (valid token) | `{"id": 1, "username": "admin"}` — no password |
| `GET /ping?ip=127.0.0.1;whoami` | `400 Invalid IP` |
| `GET /config` | `{"status": "OK"}` — no secrets |

---

## 🏗️ Phase 6: Infrastructure as Code (Terraform)

All Azure infrastructure is defined and managed as code.

```hcl
# Resources provisioned
azurerm_resource_group        → devsecops-rg
azurerm_container_registry    → devsecopsakr123
azurerm_kubernetes_cluster    → devsecops-aks
azurerm_role_assignment       → AcrPull (AKS → ACR)
```

```bash
cd infra
terraform init
terraform plan
terraform apply
```

---

## 🔑 Key Security Principles Demonstrated

- **Shift-Left Security** — vulnerabilities caught in CI before they reach production
- **Security as Code** — pipeline enforces policy automatically on every commit
- **Least Privilege** — AKS only has AcrPull permission, not full ACR access
- **Secrets Management** — no credentials in code or manifests; environment variables and Kubernetes Secrets used
- **Defense in Depth** — multiple scanning layers (SAST + SCA + container + secrets)
- **Before vs After** — vulnerable baseline documented and compared against remediated version

---

## 🚀 Running Locally

```bash
# Clone the repo
git clone https://github.com/Lhilove/devsecops-azure-project.git
cd devsecops-azure-project

# Build and run with Docker
docker build -t devsecops-app .
docker run -p 5000:5000 \
  -e ADMIN_TOKEN=your_token \
  -e USER_TOKEN=your_token \
  devsecops-app

# Test
curl http://localhost:5000
```

---

## 📋 What This Project Proves

> "I built a system that **prevents** insecure code from reaching production — not one that finds problems after the fact."

- ✅ Designed and built a vulnerable app to validate security controls
- ✅ Implemented automated security gates in CI/CD that block deployments
- ✅ Remediated OWASP Top 10 vulnerabilities with documented before/after
- ✅ Deployed a containerized workload to Azure Kubernetes Service
- ✅ Provisioned cloud infrastructure reproducibly with Terraform
- ✅ Managed secrets properly across code, pipeline, and Kubernetes

---

## 👤 Author

**Adepelumi** — Application Security | DevSecOps  
GitHub: [@Lhilove](https://github.com/Lhilove)