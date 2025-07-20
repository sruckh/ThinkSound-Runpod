FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    git \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu126 torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
    && wget https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.1.post4/flash_attn-2.7.1.post4+cu11torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl \
    && pip install --no-cache-dir flash_attn-2.7.1.post4+cu11torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl \
    && rm flash_attn-2.7.1.post4+cu11torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl \
    && pip install --no-cache-dir packaging \
    && pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1 \
    HF_TOKEN="" \
    GRADIO_SHARE=false

EXPOSE 7860

CMD ["/bin/bash", "startup.sh"]