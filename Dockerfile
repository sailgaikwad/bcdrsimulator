FROM python:3.14-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ /app/app/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

# Run Streamlit on the specified PORT
ENTRYPOINT ["sh", "-c", "streamlit run app/main.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true"]
