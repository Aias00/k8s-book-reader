#!/bin/sh
# Linux CI only. This creates and deletes its own isolated kind cluster.
set -eu
cd "$(dirname "$0")/.."
mkdir -p .tools .build research
curl -fLsS --retry 3 https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-linux-amd64 -o .tools/kind-linux-amd64
curl -fLsS --retry 3 https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-linux-amd64.sha256sum -o .tools/kind.sha256sum
(cd .tools && sha256sum -c kind.sha256sum)
chmod +x .tools/kind-linux-amd64
curl -fLsS --retry 3 https://dl.k8s.io/release/v1.37.0/bin/linux/amd64/kubectl -o .tools/kubectl
curl -fLsS --retry 3 https://dl.k8s.io/release/v1.37.0/bin/linux/amd64/kubectl.sha256 -o .tools/kubectl.sha256
echo "$(cat .tools/kubectl.sha256)  .tools/kubectl" | sha256sum -c
chmod +x .tools/kubectl
export PATH="$PWD/.tools:$PATH"
export KUBECONFIG="$PWD/.build/kubeconfig"
if .tools/kind-linux-amd64 get clusters | grep -qx 'k8s-book'; then
  echo 'Refusing to replace an existing k8s-book cluster' >&2
  exit 1
fi
cleanup() {
  kubectl --context kind-k8s-book -n k8s-book get pods,services,pvc -o wide > .build/kind-summary.txt 2>&1 || true
  .tools/kind-linux-amd64 delete cluster --name k8s-book
}
trap cleanup EXIT
.tools/kind-linux-amd64 create cluster --name k8s-book --wait 180s \
  --image kindest/node:v1.37.0@sha256:a1ed56cfb0e7b93589bdf97c8cd566405a265939e3620fc4f5de89adff580ae5
python3 lab/run_kind.py
