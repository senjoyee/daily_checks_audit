# Use a lightweight Python base image
FROM python:3.13-slim

# Install uv for dependency management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev

# Copy source code and skills
COPY src ./src
COPY .agent/skills/daily-checks-audit/scripts ./.agent/skills/daily-checks-audit/scripts
COPY .agent/skills/daily-checks-audit/configs ./.agent/skills/daily-checks-audit/configs

# Expose the port
EXPOSE 8000

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# Run the server using uvicorn
CMD ["uvicorn", "src.server_http:app", "--host", "0.0.0.0", "--port", "8000"]
