FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/
RUN useradd -ms /bin/bash jarvis && chown -R jarvis:jarvis /app
USER jarvis
CMD ["python", "web_jarvis.py"]