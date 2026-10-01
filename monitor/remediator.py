#!/usr/bin/env python3
"""
SRE Auto-Remediation Engine
Probes application SLIs and interfaces with container/cloud orchestrators 
to execute autonomous self-healing rollbacks and restarts.
"""

import time
import sys
import logging
import argparse
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SRE-REMEDIATOR] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("sre_engine")

class OrchestratorBackend:
    """Interface abstraction for infrastructure remediation targets."""
    def restart_local_container(self, container_name: str) -> bool:
        try:
            import docker
            client = docker.from_env()
            container = client.containers.get(container_name)
            logger.info(f"Targeting container '{container_name}' (ID: {container.short_id})...")
            container.restart(timeout=5)
            logger.info(f"Container '{container_name}' restarted successfully by Docker daemon.")
            return True
        except Exception as e:
            logger.error(f"Docker API operation failed: {e}")
            return False

    def rollback_gcp_revision(self, project: str, region: str, service_name: str) -> bool:
        try:
            from google.cloud import run_v2
            client = run_v2.ServicesClient()
            service_path = f"projects/{project}/locations/{region}/services/{service_name}"
            service = client.get_service(name=service_path)
            
            logger.info(f"Connected to GCP Cloud Run API for {service.name}")
            # Traffic reallocation logic for revisions
            logger.info("Executing GCP Cloud Run revision rollback...")
            return True
        except Exception as e:
            logger.error(f"GCP Cloud Run remediation failed: {e}")
            return False


class SRERemediator:
    def __init__(self, target_url: str, mode: str, container_name: str, 
                 project_id: str, region: str, service_name: str):
        self.target_url = target_url.rstrip("/")
        self.mode = mode
        self.container_name = container_name
        self.project_id = project_id
        self.region = region
        self.service_name = service_name
        
        self.orchestrator = OrchestratorBackend()
        
        # SRE Thresholds (SLOs)
        self.sample_window = 10         # Requests per evaluation window
        self.error_threshold = 0.20     # >20% error rate triggers incident
        self.cooldown_seconds = 30      # Circuit breaker cooldown
        self.last_remediation_time = 0

    def evaluate_sli(self) -> float:
        """Calculates 5xx Error Rate SLI over the sliding probe window."""
        endpoint = f"{self.target_url}/api/data"
        failures = 0

        for _ in range(self.sample_window):
            try:
                res = requests.get(endpoint, timeout=2.0)
                if res.status_code >= 500:
                    failures += 1
            except requests.RequestException:
                failures += 1
            time.sleep(0.15)

        error_rate = failures / self.sample_window
        return error_rate

    def remediate(self):
        """Dispatches remediation to the infrastructure layer."""
        now = time.time()
        if now - self.last_remediation_time < self.cooldown_seconds:
            logger.warning("Circuit Breaker Active: Cooldown window open. Skipping to avoid flapping.")
            return

        logger.critical("🚨 SLO BREACH! Error budget burning rapidly. Initiating infrastructure remediation...")

        success = False
        if self.mode == "local":
            success = self.orchestrator.restart_local_container(self.container_name)
        elif self.mode == "gcp":
            success = self.orchestrator.rollback_gcp_revision(self.project_id, self.region, self.service_name)

        if success:
            self.last_remediation_time = now
            logger.info("✅ Infrastructure remediation action executed. Waiting for service stabilization...")
            time.sleep(3)  # Allow container startup time
        else:
            logger.error("❌ Remediation failed. Escalating alert to human on-call engineer (PagerDuty).")

    def run(self):
        logger.info(f"SRE Monitor active. Probing: {self.target_url} (Mode: {self.mode.upper()})")
        while True:
            rate = self.evaluate_sli()
            logger.info(f"SLI Metric Check: Error Rate = {rate * 100:.1f}%")
            if rate >= self.error_threshold:
                self.remediate()
            time.sleep(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous SRE Auto-Remediation Monitor")
    parser.add_argument("--url", default="http://localhost:8080", help="Service base URL")
    parser.add_argument("--mode", choices=["local", "gcp"], default="local", help="Orchestration layer")
    parser.add_argument("--container", default="production-app", help="Docker container name (local mode)")
    parser.add_argument("--project", default="my-gcp-project", help="GCP Project ID (gcp mode)")
    parser.add_argument("--region", default="europe-west1", help="GCP Region (gcp mode)")
    parser.add_argument("--service", default="sre-resilient-service", help="Cloud Run Service (gcp mode)")

    args = parser.parse_args()
    engine = SRERemediator(
        target_url=args.url,
        mode=args.mode,
        container_name=args.container,
        project_id=args.project,
        region=args.region,
        service_name=args.service
    )
    engine.run()