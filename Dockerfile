FROM nvidia/cuda:12.6.0-cudnn9-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1 \
    HF_TOKEN="" \
    GRADIO_SHARE=false

EXPOSE 7860

CMD ["/bin/bash", "startup.sh"]