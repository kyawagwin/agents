"""Main Entrypoint for Agile Dev Crew (Pod Architecture).

Executes Approach 3: Hierarchical Cross-Functional Pod Sprint Flow:
- Pod A: Product & Design Pod (Product Owner + UI/UX Designer)
- Pod B: Engineering Pod (System Architect Manager + Backend & Frontend Developers)
- Pod C: Quality & Delivery Pod (QA Engineer + DevOps Release Lead)
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from agile_dev_crew.crew import AgileDevCrew
from agile_dev_crew.flow import HierarchicalPodSprintFlow
from agile_dev_crew.schemas import SprintReleasePackage

SAMPLE_REQUIREMENTS = (
    "Design and implement a full-stack, cloud-native Webhook Dispatcher & Event Delivery Platform. "
    "The system consists of:\n"
    "1. Backend (FastAPI + PostgreSQL): Ingest JSON event payloads with HMAC-SHA256 signature verification, "
    "persist subscription destinations, provide asynchronous webhook delivery with exponential backoff retries, "
    "circuit breaker protection, and REST API endpoints for event publishing and audit logs.\n"
    "2. Frontend (Next.js 14 + Tailwind CSS): Modern developer portal with subscription dashboard, real-time "
    "delivery attempt logs, status badges, payload inspector, and endpoint configuration forms conforming "
    "to WCAG 2.1 AA accessibility standards."
)


def run_flow() -> None:
    """Executes Approach 3: Multi-Pod Sprint Flow with hierarchical engineering and QA rework."""
    load_dotenv()
    os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

    print("=" * 80)
    print("🌊 INITIALIZING MULTI-POD SPRINT FLOW (APPROACH 3)")
    print("=" * 80)
    print(f"Target Feature Specification:\n{SAMPLE_REQUIREMENTS}\n")
    print("Multi-Pod Architecture:")
    print("  🎨 Pod A (Product & Design): Product Owner + UI/UX Designer")
    print("  ⚙️ Pod B (Full-Stack Engineering): System Architect (Lead) + Backend & Frontend Devs")
    print("  🧪 Pod C (Quality & Platform): QA Engineer + DevOps Release Lead")
    print("  🔁 Router: Self-healing loop directing QA defects back to Pod B until sign-off.\n")

    # Instantiate the multi-pod flow
    flow = HierarchicalPodSprintFlow()
    flow.state.project_requirements = SAMPLE_REQUIREMENTS
    flow.state.max_iterations = 3

    # Kick off the multi-pod sprint
    result = flow.kickoff()

    print("\n" + "=" * 80)
    print("🏁 MULTI-POD SPRINT FLOW EXECUTION FINISHED")
    print("=" * 80)

    if isinstance(result, SprintReleasePackage):
        _display_and_export_artifacts(result, flow)
    elif flow.state.release_package:
        _display_and_export_artifacts(flow.state.release_package, flow)
    else:
        print("Flow Result:", result)


def run() -> None:
    """Executes the 7-agent unified sequential Crew pipeline."""
    load_dotenv()
    os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

    inputs = {"project_requirements": SAMPLE_REQUIREMENTS}

    print("=" * 80)
    print("🚀 INITIALIZING UNIFIED 7-AGENT CREW PIPELINE")
    print("=" * 80)

    crew_instance = AgileDevCrew()
    crew_runner = crew_instance.crew()
    result = crew_runner.kickoff(inputs=inputs)

    print("\n" + "=" * 80)
    print("🏁 UNIFIED CREW PIPELINE COMPLETE")
    print("=" * 80)

    if hasattr(result, "pydantic") and isinstance(result.pydantic, SprintReleasePackage):
        _display_and_export_artifacts(result.pydantic)
    else:
        print("Raw Task Output:")
        print(result.raw if hasattr(result, "raw") else str(result))


def _display_and_export_artifacts(release: SprintReleasePackage, flow: HierarchicalPodSprintFlow = None) -> None:
    """Renders the executive sprint review and saves deployment assets to disk."""
    rework_count = flow.state.iteration_count if flow else 0

    print(f"\n📦 RELEASE VERSION: {release.release_version}")
    print(f"🎯 SPRINT GOAL: {release.sprint_goal}")
    print(f"🔄 REWORK CYCLES COMPLETED: {rework_count}")
    print(f"📊 RELEASE READINESS SCORE: {release.release_readiness_score}/100.0")
    print(f"✅ RELEASE SIGNOFF: {'APPROVED FOR PRODUCTION' if release.release_signoff else 'BLOCKED'}")

    print("\n--- SPRINT REVIEW SUMMARY ---")
    print(release.sprint_review_summary)

    print("\n--- RETROSPECTIVE OBSERVATIONS (KAIZEN) ---")
    for idx, obs in enumerate(release.retrospective_observations, start=1):
        print(f"  {idx}. {obs}")

    output_dir = Path("output/deployment")
    output_dir.mkdir(parents=True, exist_ok=True)

    backend_dockerfile = output_dir / "Dockerfile.backend"
    frontend_dockerfile = output_dir / "Dockerfile.frontend"
    docker_compose_path = output_dir / "docker-compose.yml"
    github_workflow_dir = output_dir / ".github" / "workflows"
    github_workflow_dir.mkdir(parents=True, exist_ok=True)
    github_ci_path = github_workflow_dir / "ci.yml"
    env_example_path = output_dir / ".env.example"
    summary_path = output_dir / "sprint_review.json"

    backend_dockerfile.write_text(release.deployment_artifacts.dockerfile_backend)
    frontend_dockerfile.write_text(release.deployment_artifacts.dockerfile_frontend)
    docker_compose_path.write_text(release.deployment_artifacts.docker_compose_content)
    github_ci_path.write_text(release.deployment_artifacts.github_actions_ci_cd)
    env_example_path.write_text(release.deployment_artifacts.env_template)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(release.model_dump(), f, indent=2)

    print(f"\n💾 Full-Stack deployment assets successfully written to '{output_dir.resolve()}':")
    print(f"   - {backend_dockerfile.name}")
    print(f"   - {frontend_dockerfile.name}")
    print(f"   - {docker_compose_path.name}")
    print(f"   - {github_ci_path.relative_to(output_dir)}")
    print(f"   - {env_example_path.name}")
    print(f"   - {summary_path.name}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--linear":
        run()
    else:
        run_flow()
