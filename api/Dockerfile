FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    cmake \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

ENV CMAKE_ARGS="-DLLAMA_CUDA=on"
ENV FORCE_CMAKE=1

RUN pip install --upgrade pip setuptools wheel && \
    pip install llama-cpp-python --no-cache-dir

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]