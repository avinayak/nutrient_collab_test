# Use a Python image
FROM python:3.12-slim

# Install uv directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation and copy linking for performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: ensures the lockfile is strictly respected
# --no-dev: excludes development dependencies (like pytest)
# --no-install-project: installs libs only, not your app code yet
RUN uv sync --frozen --no-dev --no-install-project

# Add the virtual environment to PATH
# This allows you to run "gunicorn" directly without activating
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of your application code
COPY . .

# (Optional) Install the project itself if it's a package
# RUN uv sync --frozen --no-dev

# Expose the port
EXPOSE 8080

# Start the app
# Ensure 'app:app' matches your file name and Flask instance name
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]