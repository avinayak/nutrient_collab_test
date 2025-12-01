# Use a Python image
FROM python:3.12-slim

# Install uv directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation and copy linking for performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy all files (needed for installation)
COPY . .

# Install dependencies system-wide
# This avoids venv path issues and makes binaries immediately available
RUN uv pip install --system -r pyproject.toml

# Expose the port
EXPOSE 8080

# Start the app
# Ensure 'app:app' matches your file name and Flask instance name
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]