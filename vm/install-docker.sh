#!/bin/bash
set -euo pipefail

# Выполняется внутри новой Ubuntu VM от обычного пользователя.
# Установка из официального apt-репозитория Docker.
sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl git ufw openssh-server
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
vm_arch="$(dpkg --print-architecture)"
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $vm_arch
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
sudo systemctl enable --now docker ssh
sudo ufw allow OpenSSH
sudo ufw allow 8084/tcp
sudo ufw --force enable
sudo docker --version
sudo docker compose version
echo "Docker установлен. Переподключитесь по SSH, чтобы обновились группы пользователя."
