FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app

COPY src/protection_layers ./src/protection_layers

# Make port 80 available to the world outside this container
EXPOSE 8501

CMD ["streamlit", "run", "/app/app.py"]