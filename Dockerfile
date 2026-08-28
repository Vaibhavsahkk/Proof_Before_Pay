FROM python:3.12-slim@sha256:09f7da3bc104798d0afb40bc08d23ab2da20a76130cec1f2ef170848f5d85217

WORKDIR /app

COPY requirements.lock requirements.txt ./
RUN pip install --no-cache-dir -r requirements.lock

COPY . .

RUN useradd -m micro1user && chown -R micro1user:micro1user /app
USER micro1user

CMD ["python", "-m", "src.main", "--smoke"]
