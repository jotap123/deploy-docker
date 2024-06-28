# Use a imagem base do Ubuntu 22.04
FROM ubuntu:22.04

# Atualize os pacotes e instale as dependências necessárias
RUN apt-get update && apt-get install -y \
    wget \
    bzip2 \
    ca-certificates \
    libglib2.0-0 \
    libxext6 \
    libsm6 \
    libxrender1 \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Faça o download e instale o Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh \
    && bash ~/miniconda.sh -b -p /opt/conda \
    && rm ~/miniconda.sh

# Adicione o Miniconda ao PATH
ENV PATH=/opt/conda/bin:$PATH

COPY requirements.txt /app/requirements.txt

RUN conda create --quiet -y --name app python==3.12 && conda clean -afy
RUN /opt/conda/envs/app/bin/pip install -r /app/requirements.txt

COPY dags /app/dags
COPY run.py dags.yaml /app/

WORKDIR /app/

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "app", "bash", "-c"]
