---
name: docker
description: Manage Docker containers, images, volumes, networks, and Compose stacks. Build, run, debug, and clean up containerized applications.
version: 1.0.0
author: Tugrul Guner
license: MIT
metadata:
  hermes:
    tags: [Docker, Containers, DevOps, Compose, Images, Deployment]
    related_skills: [github-pr-workflow, systematic-debugging]
---

# Docker Management

Complete guide for managing Docker containers, images, volumes, networks, and Compose stacks via the CLI.

## Prerequisites

- Docker Engine installed and running
- User in the `docker` group (or use `sudo`)

### Quick Check

```bash
docker version --format '{{.Server.Version}}' 2>/dev/null || echo "Docker not running"
docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || echo "Compose not available"
```

---

## 1. Container Lifecycle

### Run a Container

```bash
# Basic run (foreground)
docker run --name myapp -p 8080:80 nginx:alpine

# Detached with auto-restart
docker run -d --name myapp --restart unless-stopped -p 8080:80 nginx:alpine

# With environment variables and volume mount
docker run -d --name mydb \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=myapp \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:16-alpine
```

### List / Inspect / Logs

```bash
# Running containers
docker ps

# All containers (including stopped)
docker ps -a

# Detailed inspection
docker inspect myapp | jq '.[0].NetworkSettings.IPAddress'

# Follow logs
docker logs -f --tail 100 myapp

# Logs with timestamps
docker logs --timestamps --since 1h myapp
```

### Stop / Start / Restart / Remove

```bash
docker stop myapp
docker start myapp
docker restart myapp

# Remove (must be stopped first, or use -f)
docker rm myapp
docker rm -f myapp

# Remove all stopped containers
docker container prune -f
```

### Execute Commands Inside

```bash
# Interactive shell
docker exec -it myapp /bin/sh

# Run a one-off command
docker exec myapp cat /etc/nginx/nginx.conf

# As root (if container runs as non-root)
docker exec -u root -it myapp /bin/sh
```

---

## 2. Images

### Build

```bash
# Build from Dockerfile in current directory
docker build -t myapp:latest .

# Build with build args and no cache
docker build --no-cache --build-arg NODE_ENV=production -t myapp:v1.2.0 .

# Multi-platform build (requires buildx)
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest --push .
```

### List / Pull / Push

```bash
# List local images
docker images

# Pull specific tag
docker pull python:3.11-slim

# Tag and push to registry
docker tag myapp:latest registry.example.com/myapp:v1.2.0
docker push registry.example.com/myapp:v1.2.0
```

### Clean Up

```bash
# Remove dangling images
docker image prune -f

# Remove ALL unused images (not just dangling)
docker image prune -a -f

# Remove specific image
docker rmi myapp:old-tag
```

---

## 3. Docker Compose

### Basic Operations

```bash
# Start all services (detached)
docker compose up -d

# Start and rebuild if Dockerfiles changed
docker compose up -d --build

# Stop all services
docker compose down

# Stop and remove volumes (DESTRUCTIVE — removes data)
docker compose down -v

# View status
docker compose ps

# View logs for a specific service
docker compose logs -f api
```

### Scaling and Exec

```bash
# Scale a service
docker compose up -d --scale worker=3

# Exec into a specific service
docker compose exec api /bin/sh

# Run a one-off command in a service
docker compose run --rm api python manage.py migrate
```

### Compose File Validation

```bash
# Validate docker-compose.yml
docker compose config

# Show resolved config (with env var substitution)
docker compose config --resolve-image-digests
```

---

## 4. Volumes and Networks

### Volumes

```bash
# List volumes
docker volume ls

# Create a named volume
docker volume create mydata

# Inspect a volume (find mount point)
docker volume inspect mydata

# Remove unused volumes
docker volume prune -f
```

### Networks

```bash
# List networks
docker network ls

# Create a custom network
docker network create mynet

# Connect a running container to a network
docker network connect mynet myapp

# Inspect network (see connected containers)
docker network inspect mynet
```

---

## 5. Debugging Containers

### Container Won't Start

```bash
# Check exit code and error
docker ps -a --filter "name=myapp"
docker logs myapp

# Inspect the container state
docker inspect myapp | jq '.[0].State'

# Start with entrypoint override to debug
docker run -it --entrypoint /bin/sh myapp:latest
```

### Resource Usage

```bash
# Live resource stats
docker stats

# Stats for specific container (no stream)
docker stats --no-stream myapp
```

### File System Inspection

```bash
# Copy file from container to host
docker cp myapp:/app/config.json ./config.json

# Copy file from host to container
docker cp ./fix.py myapp:/app/fix.py

# View filesystem changes since container start
docker diff myapp
```

---

## 6. System Maintenance

### Disk Usage

```bash
# Show Docker disk usage breakdown
docker system df

# Detailed breakdown
docker system df -v
```

### Full Cleanup

```bash
# Remove ALL unused data (stopped containers, unused networks, dangling images, build cache)
docker system prune -f

# Nuclear option: also remove unused volumes and all unused images
docker system prune -a --volumes -f
```

---

## 7. Common Patterns

### Dockerfile Best Practices

```dockerfile
# Use specific tags, not :latest
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency files first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Non-root user
RUN useradd -m appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080
CMD ["python", "app.py"]
```

### Wait for Dependencies

```bash
# Wait for a service to be ready before starting
docker compose exec api sh -c 'until pg_isready -h db -U postgres; do sleep 1; done'
```

## Pitfalls

- **Forgetting -d**: Running without `-d` blocks the terminal. Use `-d` for background.
- **Volume data loss**: `docker compose down -v` removes named volumes. Only use when you want to reset data.
- **Layer caching**: Put frequently changing files (source code) AFTER rarely changing files (dependencies) in Dockerfile.
- **Image bloat**: Use multi-stage builds for compiled languages. Use `-slim` or `-alpine` base images.
- **Dangling images**: Build frequently? Run `docker image prune -f` periodically.
- **Port conflicts**: Check `docker ps` before binding a port. Use `docker port myapp` to see mappings.
