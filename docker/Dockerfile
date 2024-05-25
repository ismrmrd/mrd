FROM ubuntu:22.04 AS base

RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

ARG USERNAME="mrd"
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG CONDA_GID=900

# Create mrd user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

ARG MINIFORGE_NAME=Miniforge3
ARG MINIFORGE_VERSION=24.3.0-0
ARG CONDA_DIR=/opt/conda

# Install mamba (conda)
# Based on https://github.com/conda-forge/miniforge-images/blob/master/ubuntu/Dockerfile
RUN wget --no-hsts --quiet https://github.com/conda-forge/miniforge/releases/download/${MINIFORGE_VERSION}/${MINIFORGE_NAME}-${MINIFORGE_VERSION}-Linux-$(uname -m).sh -O /tmp/miniforge.sh \
    && /bin/bash /tmp/miniforge.sh -b -p ${CONDA_DIR} \
    && rm /tmp/miniforge.sh \
    && ${CONDA_DIR}/bin/conda clean --tarballs --index-cache --packages --yes \
    && find ${CONDA_DIR} -follow -type f -name '*.a' -delete \
    && find ${CONDA_DIR} -follow -type f -name '*.pyc' -delete \
    && ${CONDA_DIR}/bin/conda clean --force-pkgs-dirs --all --yes  \
    && groupadd -r conda --gid ${CONDA_GID} \
    && usermod -aG conda ${USERNAME} \
    && chown -R :conda ${CONDA_DIR} \
    && chmod -R g+w ${CONDA_DIR} \
    && find /opt -type d | xargs -n 1 chmod g+s

# Create mrd conda environment
COPY --chown=$USER_UID:conda environment.yml /tmp/build/
RUN umask 0002 \
    && ${CONDA_DIR}/bin/mamba env create -f /tmp/build/environment.yml \
    && ${CONDA_DIR}/bin/mamba clean -fy \
    && chown -R :conda ${CONDA_DIR}/envs

# Build mrd C++ tools
COPY ./cpp /opt/code/mrd
RUN . ${CONDA_DIR}/etc/profile.d/conda.sh && umask 0002 && conda activate mrd && \
    cd /opt/code/mrd && \
    rm -rf ./build && \
    mkdir ./build && \
    cd ./build && \
    cmake -G Ninja -D CMAKE_CXX_STANDARD=17 -D CMAKE_INSTALL_PREFIX=${CONDA_DIR}/envs/mrd .. && \
    ninja install

COPY docker/entrypoint.sh /opt/
RUN sed -i 's/\r$//' /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

FROM base AS mrd-tools

ENTRYPOINT [ "/opt/entrypoint.sh" ]
