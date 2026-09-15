FROM python:3.11-slim

# تثبيت ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت المكتبات
RUN pip install --no-cache-dir \
    pyTelegramBotAPI==4.14.0 \
    Pillow==10.2.0

# نسخ كود البوت
COPY bot.py .

CMD ["python", "bot.py"]
