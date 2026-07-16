#!/usr/bin/env bash
# End-to-end smoke test: build images, stand up a local KinD cluster, deploy
# the Helm chart, trigger one scrape, and confirm the API serves real data.
# Requires: docker, kind, helm, kubectl. Cleans up the cluster on exit.
set -euo pipefail

CLUSTER_NAME="jobless-smoke"

cleanup() {
  kind delete cluster --name "$CLUSTER_NAME" || true
}
trap cleanup EXIT

echo "==> Building images"
docker build -t jobless-api -f Dockerfile .
docker build -t jobless-scraper -f Dockerfile.scraper .

echo "==> Creating KinD cluster"
kind create cluster --name "$CLUSTER_NAME"

echo "==> Loading images into the cluster"
kind load docker-image jobless-api:latest jobless-scraper:latest --name "$CLUSTER_NAME"

echo "==> Installing the Helm chart"
helm install jobless charts/jobless --create-namespace --namespace jobless \
  --kube-context "kind-$CLUSTER_NAME" --wait --timeout 3m

echo "==> Triggering one scrape run"
kubectl create job --from=cronjob/jobless-scraper smoke-test-run -n jobless
kubectl wait --for=condition=complete job/smoke-test-run -n jobless --timeout=5m

echo "==> Checking the API"
kubectl port-forward -n jobless svc/jobless-api 8080:80 >/dev/null 2>&1 &
PF_PID=$!
trap "kill $PF_PID 2>/dev/null || true; cleanup" EXIT
sleep 3

health=$(curl -sf http://localhost:8080/health)
echo "health: $health"

jobs_count=$(curl -sf "http://localhost:8080/jobs?limit=1" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
if [ "$jobs_count" -lt 1 ]; then
  echo "FAILED: /jobs returned no rows after a scrape run"
  exit 1
fi

echo "==> Smoke test passed: API is healthy and serving scraped jobs"
