FROM python:3.11-slim

WORKDIR /app

# Install system deps for faiss and any OS-level requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app code
COPY . /app

# Expose Streamlit and API ports
EXPOSE 8501 8000

CMD ["bash","-lc","streamlit run Youtube_Chatbot/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
