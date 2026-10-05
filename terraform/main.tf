terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
}

provider "docker" {
  host = var.docker_host
}

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
resource "docker_network" "facilities_net" {
  name = "facilities-net-${var.group_id}"
}

# ---------------------------------------------------------------------------
# Data Volume
# ---------------------------------------------------------------------------
resource "docker_volume" "facilities_data" {
  name = "facilities-data-${var.group_id}"
}

# ---------------------------------------------------------------------------
# Image Reference
# ---------------------------------------------------------------------------
# This expects the image to already be built by Jenkins or manually
data "docker_image" "facilities_img" {
  name = "${var.image_name}:latest"
}

# ---------------------------------------------------------------------------
# API Container
# ---------------------------------------------------------------------------
resource "docker_container" "api" {
  name  = "facilities-api-${var.group_id}"
  image = data.docker_image.facilities_img.name

  # Override CMD if needed, though Dockerfile defaults to api
  command = ["uvicorn", "facilities.api:app", "--host", "0.0.0.0", "--port", "8000"]

  networks_advanced {
    name = docker_network.facilities_net.name
    aliases = ["api"]
  }

  volumes {
    volume_name    = docker_volume.facilities_data.name
    container_path = "/data"
  }

  ports {
    internal = 8000
    external = 8002
    ip       = "127.0.0.1"
  }

  env = [
    "PROVIDER_MODE=${var.provider_mode}",
    "LM_STUDIO_URL=${var.lm_studio_url}",
    "MODEL_NAME=${var.model_name}",
    "DATABASE_PATH=/data/facilities.db"
  ]
}

# ---------------------------------------------------------------------------
# UI Container
# ---------------------------------------------------------------------------
resource "docker_container" "ui" {
  name  = "facilities-ui-${var.group_id}"
  image = data.docker_image.facilities_img.name

  command = ["streamlit", "run", "streamlit_app.py", "--server.port", "8502", "--server.address", "0.0.0.0"]

  networks_advanced {
    name = docker_network.facilities_net.name
  }

  ports {
    internal = 8502
    external = 8502
    ip       = "127.0.0.1"
  }

  env = [
    # The UI talks to the API container via Docker DNS alias 'api'
    "API_URL=http://api:8000"
  ]

  # Ensure API starts first
  depends_on = [docker_container.api]
}
