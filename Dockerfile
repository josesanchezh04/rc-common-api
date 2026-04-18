# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /build

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias en directorio local del usuario
RUN pip install --no-cache-dir --user --compile -r requirements.txt


# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Crear usuario no-root
RUN useradd -m -u 1000 -s /bin/bash appuser

# Copiar dependencias desde builder
COPY --from=builder /root/.local /home/appuser/.local

# Asegurar PATH correcto
ENV PATH=/home/appuser/.local/bin:$PATH

# Copiar código
COPY --chown=appuser:appuser src/ ./src/

# Cambiar a usuario no-root
USER appuser

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    ENV=production

# Puerto dinámico (Cloud Run usa PORT)
ENV PORT=4000

# Healthcheck con timeout (importante)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get(f'http://localhost:{__import__(\"os\").environ.get(\"PORT\", 4000)}/health', timeout=2.0)" || exit 1

# Exponer puerto (documentativo)
EXPOSE 4000

# Startup dinámico (compatible con Cloud Run)
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}"]