# Facilities Request Triage (Group 02)

## Objective
This project provides an AI-powered local facilities request triage application for university campuses. It receives maintenance requests and deterministically categorises them (electrical, plumbing, heating), assigns a priority (low, medium, high), writes a summary, proposes the next action, and ensures that all AI-generated actions are flagged as requiring human review. It strictly avoids offering repair instructions.

## Architecture
The application adopts a robust microservice architecture:
- **Streamlit UI**: Provides the user-facing dashboard for submitting requests and viewing history.
- **FastAPI**: Manages input/output validation, orchestration, and state persistence.
- **SQLite Database**: Persists validated triage records in a local data volume.
- **AnalysisService (Pydantic / Provider Interface)**: Validates requirements and orchestrates between mock models for CI and LM Studio for real inference.
- **LM Studio (Qwen3-VL-8B)**: Handles the local Large Language Model inference cleanly abstracted behind the Provider interface.

## Installation
The project relies on Docker for encapsulation.
Requirements:
- Git
- Docker and Docker Compose (or `kreuzwerker/docker` Terraform provider)
- Terraform
- LM Studio

Clone the repository:
```bash
git clone <repository-url> facilities-g02
cd facilities-g02
```

## LM Studio & Qwen3-VL-8B Configuration
1. Open LM Studio and download the `Qwen3-VL-8B` model.
2. Start the local inference server in LM Studio on `http://localhost:1234/v1`.
3. In the `.env` file, ensure you have:
```env
LM_STUDIO_URL=http://host.docker.internal:1234/v1
MODEL_NAME=qwen3-vl-8b
PROVIDER_MODE=lmstudio
```
*(Note: `host.docker.internal` allows Docker containers to route to the host's localhost).*

## Run Instructions
### Using Terraform (Recommended)
You can spin up the entire application stack using Terraform:
```bash
cd terraform
terraform init
terraform plan
terraform apply -auto-approve
```
The API will be available at `http://127.0.0.1:8002` and the UI at `http://127.0.0.1:8502`.

To tear down the infrastructure:
```bash
terraform destroy
```

### Using Local Python Environment (Development)
If you wish to run it locally without Docker:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn facilities.api:app --reload --port 8000 &
streamlit run streamlit_app.py --server.port 8502
```

## Tests
The testing framework is built on `pytest`. It relies on the deterministic MockProvider to ensure reproducible runs without needing an active LM Studio or GPU.
To run tests locally:
```bash
pytest tests/ -v
```

## Git
Meaningful commits have been maintained. As required, a deliberate failed-test demonstration commit was pushed to test CI rules before being corrected in a subsequent commit.

## Jenkins CI
The Jenkins pipeline is defined in `Jenkinsfile` and covers:
1. Checkout
2. Python dependency installation
3. Running Pytest
4. JUnit report publishing
5. Terraform validation
6. Docker Image creation (only if tests pass)
7. Container Smoke Test on port 18002
8. Artefact Archiving

## Docker
The `Dockerfile` is a multi-stage build running an unprivileged `app` user, avoiding root privileges. It creates a named `/data` volume for the SQLite database to survive container restarts.

## Terraform
Terraform is configured with the `kreuzwerker/docker` provider to provision the Docker Network, Volumes, and the isolated API and UI containers, passing the necessary environment configuration dynamically. 

## Evidence
- Screenshots of tests passing and the Streamlit interface can be found (or added) in the evidence folder.
- Terraform plans cleanly.

## Troubleshooting
- **API Connection Refused**: Verify that Terraform successfully deployed the containers or that FastAPI is running on the correct port.
- **LM Studio Timeout / Refused**: Make sure LM Studio's Local Server is explicitly started and `host.docker.internal` resolves correctly on your operating system.
- **Failed Wheel Builds (pydantic-core)**: If running locally on Windows, ensure C++ Build Tools (MSVC) are installed, as `pydantic-core` compiles Rust extensions. Otherwise, stick to the Docker/Terraform deployment.

## Limitations
- The system heavily relies on structured JSON outputs.
- It operates under a strict categorical constraint (electrical/plumbing/heating). Ambiguous issues outside these categories will default to a fallback via the mock or be aggressively coerced by the LLM prompt.
