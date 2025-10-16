FROM python:3.11-slim

# Install uv for dependency management
RUN pip install uv

WORKDIR /app

# Copy application files
COPY . .

# Install dependencies
RUN uv pip install -e .

# Create volume mount points for multiple databases
VOLUME ["/data/sqlite", "/data/postgres", "/data/neo4j"]

# Expose ports for HTTP/SSE transport
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run FastMCP server
ENTRYPOINT ["fastmcp", "run"]
CMD ["server.py"]
