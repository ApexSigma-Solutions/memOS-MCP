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
  CMD python -c "import http.client; conn = http.client.HTTPConnection('localhost', 8080, timeout=3); conn.request('GET', '/health'); resp = conn.getresponse(); exit(0) if resp.status == 200 else exit(1)"

# Run FastMCP server
ENTRYPOINT ["fastmcp", "run"]
CMD ["server.py"]
