FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Repo clone
RUN git clone -b backend_flask_server https://github.com/50shadesofgwei/funding-rate-arbitrage.git /app

WORKDIR /app

RUN if [ -f "example.env" ]; then mv example.env .env; fi

RUN pip install --no-cache-dir -e .
EXPOSE 6969

CMD ["project-run-ui"]