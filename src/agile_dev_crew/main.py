"""Main Entrypoint for Agile Dev Crew.

Demonstrates how to inject raw business requirements into the multi-agent pipeline,
execute the autonomous sprint, and inspect the structured Pydantic outputs.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from agile_dev_crew.crew import AgileDevCrew
from agile_dev_crew.schemas import SprintReleasePackage


def run() -> None:
    """Kick off the Agile Development Crew with a production-grade feature requirement."""
    # Load environment variables from .env file
    load_dotenv()

    # Define a realistic, high-value enterprise engineering requirement
    sample_requirements = (
        "Design and implement a production-ready, cloud-native Webhook Dispatcher & Event "
        "Delivery Engine in Python using FastAPI and PostgreSQL. The service must:\n"
        "1. Ingest event payloads via REST API with HMAC-SHA256 signature verification.\n"
        "2. Persist events and target subscription destinations with status tracking.\n"
        "3. Provide asynchronous webhook dispatching with exponential backoff retries (up to 5 attempts).\n"
        "4. Implement a circuit breaker to pause deliveries to repeatedly failing endpoints.\n"
        "5. Expose REST endpoints to register subscriptions, publish events, and query delivery audit logs.\n"
        "6. Enforce strict input validation, comprehensive error handling, structured logging, and health checks."
    )

    inputs = {
        "project_requirements": sample_requirements
    }

    print("=" * 80)
    print("🚀 INITIALIZING AGILE DEV CREW: AUTONOMOUS SPRINT EXECUTION")
    print("=" * 80)
    print(f"Sprint Target:\n{sample_requirements}\n")
    print("Beginning Backlog Refinement -> Architecture -> Implementation -> QA -> Release...\n")

    # Instantiate and execute the Crew
    crew_instance = AgileDevCrew()
    crew_runner = crew_instance.crew()
    result = crew_runner.kickoff(inputs=inputs)

    print("\n" + "=" * 80)
    print("🏁 SPRINT PIPELINE EXECUTION COMPLETE")
    print("=" * 80)

    # Process and display structured release package
    if hasattr(result, "pydantic") and isinstance(result.pydantic, SprintReleasePackage):
        release_package: SprintReleasePackage = result.pydantic
        _display_and_export_artifacts(release_package)
    else:
        print("Raw Task Output:")
        print(result.raw if hasattr(result, "raw") else str(result))


def _display_and_export_artifacts(release: SprintReleasePackage) -> None:
    """Renders the executive sprint review and saves deployment assets to disk."""
    print(f"\n📦 RELEASE VERSION: {release.release_version}")
    print(f"🎯 SPRINT GOAL: {release.sprint_goal}")
    print(f"📊 RELEASE READINESS SCORE: {release.release_readiness_score}/100.0")
    print(f"✅ RELEASE SIGNOFF: {'APPROVED FOR PRODUCTION' if release.release_signoff else 'BLOCKED'}")

    print("\n--- SPRINT REVIEW SUMMARY ---")
    print(release.sprint_review_summary)

    print("\n--- RETROSPECTIVE OBSERVATIONS (KAIZEN) ---")
    for idx, obs in enumerate(release.retrospective_observations, start=1):
        print(f"  {idx}. {obs}")

    # Export generated DevOps assets to disk
    output_dir = Path("output/deployment")
    output_dir.mkdir(parents=True, exist_ok=True)

    dockerfile_path = output_dir / "Dockerfile"
    docker_compose_path = output_dir / "docker-compose.yml"
    github_workflow_dir = output_dir / ".github" / "workflows"
    github_workflow_dir.mkdir(parents=True, exist_ok=True)
    github_ci_path = github_workflow_dir / "ci.yml"
    env_example_path = output_dir / ".env.example"
    summary_path = output_dir / "sprint_review.json"

    dockerfile_path.write_text(release.deployment_artifacts.dockerfile_content)
    docker_compose_path.write_text(release.deployment_artifacts.docker_compose_content)
    github_ci_path.write_text(release.deployment_artifacts.github_actions_ci_cd)
    env_example_path.write_text(release.deployment_artifacts.env_template)
    
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(release.model_dump(), f, indent=2)

    print(f"\n💾 Production deployment assets successfully written to '{output_dir.resolve()}':")
    print(f"   - {dockerfile_path.name}")
    print(f"   - {docker_compose_path.name}")
    print(f"   - {github_ci_path.relative_to(output_dir)}")
    print(f"   - {env_example_path.name}")
    print(f"   - {summary_path.name}")


if __name__ == "__main__":
    run()
