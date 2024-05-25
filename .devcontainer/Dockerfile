ARG DEVCONTAINER_BASE=mcr.microsoft.com/devcontainers/base:1.0.23-ubuntu-22.04

#########################################################
# file-normalizer stage
# In order to use BuildKit remote caching, input files must have
# not only the right content hash, but also the right permissions.
# Git only tracks whether the owner can execute a file.
# Here we bring in all files that are going to be used in the
# subsequent stage and normalize the permissions.
#########################################################

FROM mcr.microsoft.com/oss/busybox/busybox:1.33.1 as file-normalizer

COPY environment.yml \
     .devcontainer/devcontainer.bashrc  \
     .devcontainer/matlab-r2023b.ubuntu-22.04.dependencies.txt \
     /data/

RUN chmod -R 555 /data/

#########################################################
# devcontainer stage
# Installs all dependencies and tooling for development.
#########################################################

FROM ${DEVCONTAINER_BASE} AS devcontainer

# Install needed packages and setup non-root user.
ARG USERNAME="vscode"
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG CONDA_GID=900
ARG CONDA_ENVIRONMENT_NAME=mrd

RUN apt-get update && apt-get install -y \
    libc6-dbg \
    && rm -rf /var/lib/apt/lists/*

# Setting the ENTRYPOINT to docker-init.sh will configure non-root access to
# the Docker socket if "overrideCommand": false is set in devcontainer.json.
# The script will also execute CMD if you need to alter startup behaviors.
ENTRYPOINT [ "/usr/local/share/docker-init.sh" ]
CMD [ "sleep", "infinity" ]

ARG MINIFORGE_NAME=Miniforge3
ARG MINIFORGE_VERSION=24.3.0-0
ARG CONDA_DIR=/opt/conda

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

# Create a conda environment from the environment file in the repo root.
COPY --from=file-normalizer --chown=$USER_UID:conda /data/environment.yml /tmp/build/
RUN umask 0002 \
    && ${CONDA_DIR}/bin/mamba env create -f /tmp/build/environment.yml \
    && ${CONDA_DIR}/bin/mamba clean -fy \
    && sudo chown -R :conda ${CONDA_DIR}/envs

# Add a file that is to be sourced from .bashrc and from the devops pipeline stages
COPY --from=file-normalizer /data/devcontainer.bashrc /opt/devcontainer/

# Add a section to /etc/bash.bashrc that ensures that a section is present at the end of ~/.bashrc.
# We can't just write to .bashrc from here because it will be overwritten if the devcontainer user has
# opted to use their own dotfiles repo. The dotfiles repo is cloned after the postCreateCommand
# in the devcontainer.json file is executed.
RUN echo "\n\
if ! grep -q \"^source /opt/devcontainer/devcontainer.bashrc\" \${HOME}/.bashrc; then\n\
	echo \"source /opt/devcontainer/devcontainer.bashrc\" >> \${HOME}/.bashrc\n\
fi\n" >> /etc/bash.bashrc

ENV CMAKE_GENERATOR=Ninja

# Create a kits file for the VSCode CMake Tools extension, so you are not prompted for which kit to select whenever you open VSCode
RUN . /opt/conda/etc/profile.d/conda.sh \
    && conda activate /opt/conda/envs/mrd \
    && mkdir -p /home/vscode/.local/share/CMakeTools \
    && echo "[{\"name\":\"Conda\",\"compilers\":{\"C\":\"$GCC\",\"CXX\":\"$GXX\"}}]" > /home/vscode/.local/share/CMakeTools/cmake-tools-kits.json \
    && chown vscode:conda /home/vscode/.local/share/CMakeTools/cmake-tools-kits.json


# Install the yardl tool
ARG YARDL_VERSION=0.6.0
RUN wget --quiet "https://github.com/microsoft/yardl/releases/download/v${YARDL_VERSION}/yardl_${YARDL_VERSION}_linux_x86_64.tar.gz" \
    && tar -xzf "yardl_${YARDL_VERSION}_linux_x86_64.tar.gz" \
    && mv yardl "/opt/conda/envs/${CONDA_ENVIRONMENT_NAME}/bin/" \
    && rm "yardl_${YARDL_VERSION}_linux_x86_64.tar.gz"


#########################################################
# Install Matlab
#   Based on mathworks/{matlab-deps:r2023b,matlab:r2023b}
#
# Configure the Matlab License Server to use Matlab within the devcontainer (including VSCode extensions):
#   In your HOST environment, export the environment variable MATLAB_LICENSE_FILE, e.g.
#       export MATLAB_LICENSE_FILE=/mnt/c/Users/username/Documents/MATLAB/license.lic
#########################################################

ENV DEBIAN_FRONTEND="noninteractive" TZ="Etc/UTC"

COPY --from=file-normalizer /data/matlab-r2023b.ubuntu-22.04.dependencies.txt /tmp/matlab-dependencies.txt

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install --no-install-recommends --yes \
    `cat /tmp/matlab-dependencies.txt` \
    wget \
    unzip \
    ca-certificates \
    && apt-get clean \
    && apt-get -y autoremove \
    && rm -rf /var/lib/apt/lists/*

RUN [ -d /usr/share/X11/xkb ] || mkdir -p /usr/share/X11/xkb

ARG MATLAB_RELEASE=r2023b
ARG MATLAB_PRODUCT_LIST="MATLAB"
ARG MATLAB_INSTALL_LOCATION="/opt/matlab/${MATLAB_RELEASE}"
ARG LICENSE_SERVER=

RUN adduser --shell /bin/bash --disabled-password --gecos "" matlab \
    && echo "matlab ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/matlab \
    && chmod 0440 /etc/sudoers.d/matlab

USER matlab
WORKDIR /home/matlab

ENV MLM_LICENSE_FILE=${LICENSE_SERVER}

RUN wget -q https://www.mathworks.com/mpm/glnxa64/mpm \
    && chmod +x mpm \
    && sudo HOME=${HOME} ./mpm install \
    --release=${MATLAB_RELEASE} \
    --destination=${MATLAB_INSTALL_LOCATION} \
    --products ${MATLAB_PRODUCT_LIST} \
    || (echo "MPM Installation Failure. See below for more information:" && cat /tmp/mathworks_root.log && false) \
    && sudo rm -f mpm /tmp/mathworks_root.log \
    && sudo ln -s ${MATLAB_INSTALL_LOCATION}/bin/matlab /usr/local/bin/matlab \
    && sudo ln -s ${MATLAB_INSTALL_LOCATION} /opt/matlab/latest \
    && sudo mkdir -p ${MATLAB_INSTALL_LOCATION}/licenses

# Install workaround run-matlab-command script to unify local and CI invocations of `matlab -batch`
# See https://github.com/matlab-actions/run-command/issues/53
RUN sudo wget -O /usr/local/bin/run-matlab-command https://ssd.mathworks.com/supportfiles/ci/run-matlab-command/v2/glnxa64/run-matlab-command \
    && sudo chmod +x /usr/local/bin/run-matlab-command
