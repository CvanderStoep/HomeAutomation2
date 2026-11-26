FROM python:3.14-slim

WORKDIR /usr/src/app

# Logregels direct doorgeven aan `docker logs` (niet bufferen);
# geen .pyc-bestanden schrijven (de app-map is niet schrijfbaar voor de app-gebruiker)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --chmod: leesbaar voor de app-gebruiker, ongeacht de bestandsrechten op de host
COPY --chmod=644 config.cfg .
COPY --chmod=644 *.py ./
# Secrets komen als omgevingsvariabelen uit .env; .python_hue wordt via docker-compose gemount

# Niet als root draaien. uid 1000 = gebruiker pi op de Raspberry Pi, eigenaar van .python_hue (rechten 600).
RUN useradd --uid 1000 --no-create-home --shell /usr/sbin/nologin app
USER app

CMD ["python", "realtimemonitoring.py"]
