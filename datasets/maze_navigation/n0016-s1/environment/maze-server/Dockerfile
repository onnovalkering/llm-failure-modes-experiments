FROM python:3.14-slim

RUN pip install --no-cache-dir "fastmcp~=4.1.0"

WORKDIR /srv
COPY server.py maze.json ./

EXPOSE 8000

CMD ["python", "server.py"]
