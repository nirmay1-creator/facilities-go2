variable "group_id" {
  type        = string
  description = "Group ID for resource naming"
  default     = "g02"
}

variable "docker_host" {
  type        = string
  description = "Docker daemon endpoint. Use npipe:////./pipe/docker_engine for Windows Docker Desktop, or unix:///var/run/docker.sock for Linux."
  default     = "npipe:////./pipe/docker_engine"
}

variable "image_name" {
  type        = string
  description = "Base image name built by Jenkins/Docker"
  default     = "facilities-triage-g02"
}

variable "provider_mode" {
  type        = string
  description = "Provider mode: 'lmstudio' or 'mock'"
  default     = "lmstudio"
}

variable "lm_studio_url" {
  type        = string
  description = "Actual LM Studio host address. Use host.docker.internal to reach LM Studio on the host machine from inside the container."
  default     = "http://host.docker.internal:1234/v1"
}

variable "model_name" {
  type        = string
  description = "LM Studio model name"
  default     = "qwen3-vl-8b"
}
