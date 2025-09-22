FROM bitnami/consul:1.21.3
USER root
RUN  apt-get update && apt-get install -y openssh-client && rm -rf /var/lib/apt/lists/*
RUN  apt-get update && apt-get install -y htop tree tmux curl jq wget grep gawk vim less git sudo


RUN mkdir /scratch
WORKDIR /scratch
RUN wget -q --show-progress https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
RUN /bin/bash /scratch/Miniforge3-Linux-x86_64.sh -b -p /opt/miniforge
RUN /opt/miniforge/bin/conda init -v

RUN  echo "consul:x:1001:0:consul:/home/consul:/bin/bash" >> /etc/passwd
RUN  mkdir -p /home/consul/.ssh
COPY id_rsa /home/consul/.ssh/
COPY ssh_config /home/consul/.ssh/config
RUN  chmod go-rwx /home/consul/.ssh/*
RUN  echo "alias ll='ls -Fila'" >> /home/consul/.profile
RUN  chown -Rf 1001:0 /home/consul

# set up base conda env to have requisite packages
# use data-api pacakge as proxy (has slack and a few other things)
# a bit friggy. we have to set up the ssh key for the consul checks
# same key has access to the repo already
RUN  mkdir -p /root/.ssh
RUN  echo "Host bitbucket.org" >> /root/.ssh/config
RUN  echo "    StrictHostKeyChecking no" >> /root/.ssh/config
COPY id_rsa /root/.ssh/
RUN  chmod -Rf go-rwx /root/.ssh/

RUN source ~/.bashrc && mamba install python=3.12 pip -y
RUN source ~/.bashrc && \
    pip install --no-input 'git+ssh://git@bitbucket.org/bqmrepo/data-api.git@v0.2.1#egg=bqm-data-api&subdirectory=src'

RUN  source ~/.bashrc && mamba clean -a -y
RUN  rm -Rf /scratch

RUN cat  ~/.bashrc >>  /home/consul/.bashrc

USER 1001
