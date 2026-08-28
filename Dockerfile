FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root user for security (sandboxing principle)
RUN useradd -m micro1user
USER micro1user

CMD ["python", "-m", "src.main"]
