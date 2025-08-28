FROM python:3.13-slim
WORKDIR /app

# --- START: ADDITIONS FOR HEADLESS CHROME ---

# Install essential system dependencies for Chrome.
# These libraries are required by Chrome to run in a Linux environment.
RUN apt-get update --fix-missing && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libayatana-appindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc-s1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxshmfence1 \
    libxtst6 \
    lsb-release \
     xdg-utils \
    chromium \
    chromium-driver \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*



# --- END: ADDITIONS FOR HEADLESS CHROME ---

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos "" myuser && \
    mkdir -p /app/driver-assistant/data/tool_cache && \
    chown -R myuser:myuser /app/driver-assistant/data && \
    chown -R myuser:myuser /app



COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER myuser

ENV PATH="/home/myuser/.local/bin:$PATH"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]