# Production Deployment Checklist

This document provides a checklist for deploying the MemOS FastMCP server to a production environment.

## 1. Configuration

- [ ] **Database:** Configure the database backend (PostgreSQL is recommended for production).
- [ ] **Environment Variables:** Set all required environment variables, including database credentials and secrets.
- [ ] **Logging:** Configure the log level to `INFO` or `WARNING` for production.

## 2. Docker Compose

The provided `docker-compose.yml` file is a good starting point for production deployments. You may want to customize it to fit your specific needs, such as adding a reverse proxy or configuring a different database service.

### Example with PostgreSQL

```yaml
version: '3.8'

services:
  memos-mcp:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - postgres-data:/data/postgres
    environment:
      - MEMOS_DB_TYPE=postgres
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=memos
      - POSTGRES_USER=memos_user
      - POSTGRES_PASSWORD=secure_password
    restart: unless-stopped

  postgres:
    image: postgres:13
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=memos
      - POSTGRES_USER=memos_user
      - POSTGRES_PASSWORD=secure_password

volumes:
  postgres-data:
```

## 3. Kubernetes

For large-scale deployments, Kubernetes is recommended. You will need to create your own Kubernetes manifests, but here is a basic example to get you started.

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memos-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: memos-mcp
  template:
    metadata:
      labels:
        app: memos-mcp
    spec:
      containers:
      - name: memos-mcp
        image: your-docker-registry/memos-mcp:latest
        ports:
        - containerPort: 8080
        env:
        - name: MEMOS_DB_TYPE
          value: "postgres"
        # ... other environment variables
```

## 4. Security Best Practices

- [ ] **Secrets Management:** Use a secrets management tool like HashiCorp Vault or AWS Secrets Manager to store sensitive information.
- [ ] **Network Policies:** Restrict network access to the server and database.
- [ ] **Image Scanning:** Scan the Docker image for vulnerabilities before deploying to production.

## 5. Scaling Guidelines

- [ ] **Horizontal Scaling:** The server is stateless, so you can scale it horizontally by increasing the number of replicas.
- [ ] **Database Scaling:** The database is the stateful component of the system. You will need to scale the database according to your needs.
- [ ] **Load Balancing:** Use a load balancer to distribute traffic across the server replicas.
