# Running AI Dev Squad Comparison Locally

This guide walks you through setting up the AI Dev Squad Comparison platform on your local machine using Docker and Ollama.

## Prerequisites

- Docker and Docker Compose
- At least 8GB RAM (16GB recommended)
- 50GB free disk space for models
- NVIDIA GPU (optional but recommended for better performance)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-dev-squad-comparison
   ```

2. **Start services with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the dashboard**
   Open http://localhost:8050 in your browser

## Detailed Setup

### 1. Environment Configuration

Copy the example configuration files:
```bash
cp config/system.example.yaml config/system.yaml
cp config/model_pricing.example.yaml config/model_pricing.yaml
cp config/injection_patterns.example.yaml config/injection_patterns.yaml
```

Edit `config/system.yaml` to match your environment.

### 2. Model Setup

The system will automatically download required models on first run. To pre-download:
```bash
docker-compose exec ollama ollama pull codellama:13b
docker-compose exec ollama ollama pull llama2:7b
```

### 3. VCS Integration (Optional)

See `vcs_setup.md` for GitHub and GitLab integration.

### 4. Safety Configuration

Review and customize safety policies in `config/system.yaml`.

## Services

The Docker Compose setup includes:
- **benchmark-runner**: Main application
- **ollama**: Local model server
- **jaeger**: Distributed tracing
- **dashboard**: Web interface

## Troubleshooting

See `troubleshooting.md` for common issues and solutions.

## Next Steps

- Run your first benchmark: `benchmark.md`
- Set up observability: `telemetry.md`
- Configure VCS integration: `vcs_setup.md`