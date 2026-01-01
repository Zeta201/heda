# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

# Install dependencies (including psycopg2-binary)
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

# Stage 2: Final runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy app code
COPY --from=builder /app/app ./app

# Set PATH so Python packages are found
ENV PATH=/root/.local/bin:$PATH

# Expose API port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
