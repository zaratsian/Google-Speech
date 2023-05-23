FROM python:3.9

WORKDIR /app

# Install container dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Copy assets into the container
COPY requirements.txt ws_server.py /app/

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7777

# Start the ws server
CMD ["python", "ws_server.py"]
