"""Main Entrypoint for Agile Dev Crew.

Supports two operational modes:
1. Event-Driven Flow (Default): Uses CrewAI Flow (@start, @listen, @router) with an autonomous
   QA rework loop routing failed reports back to the Senior Developer until all tests pass.
2. Sequential Crew Pipeline: Executes the linear 5-stage sprint pipeline from refinement to release.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from agile_dev_crew.crew import AgileDevCrew
from agile_dev_crew.flow import AgileSprintFlow
from agile_dev_crew.schemas import SprintReleasePackage

SAMPLE_REQUIREMENTS = (
    "Design and implement a production-ready, cloud-native Webhook Dispatcher & Event "
    "Delivery Engine in Python using FastAPI and PostgreSQL. The service must:\n"
    "1. Ingest event payloads via REST API with HMAC-SHA256 signature verification.\n"
    "2. Persist events and target subscription destinations with status tracking.\n"
    "3. Provide asynchronous webhook dispatching with exponential backoff retries (up to 5 attempts).\n"
    "4. Implement a circuit breaker to pause deliveries to repeatedly failing endpoints.\n"
    "5. Expose REST endpoints to register subscriptions, publish events, and query delivery audit logs.\n"
    "6. Enforce strict input validation, comprehensive error handling, structured logging, and health checks."
)


def run_flow() -> None:
    """Executes the Agile Sprint Flow with the autonomous QA rework loop."""
    load_dotenv()
    os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

    print("=" * 80)
    print("🌊 INITIALIZING AGILE SPRINT FLOW: EVENT-DRIVEN QA REWORK LOOP")
    print("=" * 80)
    print(f"Target Specification:\n{SAMPLE_REQUIREMENTS}\n")
    print("Pipeline Architecture:")
    print("  @start                  -> Product Owner & System Architect (Planning)")
    print("  @listen(or_(start, ...)) -> Senior Developer (Initial Code or QA Rework)")
    print("  @listen(implement_code) -> QA Engineer (Pytest Suites & OWASP Audit)")
    print("  @router(verify_qa)      -> Evaluates QAReport (Pass -> Release | Fail -> Rework Loop)")
    print("  @listen('qa_passed')    -> DevOps Release Lead (Dockerfile, CI/CD, Review)\n")

    # Instantiate flow with initial state
    flow = AgileSprintFlow()
    flow.state.project_requirements = SAMPLE_REQUIREMENTS
    flow.state.max_iterations = 3

    # Kick off the event-driven loop
    result = flow.kickoff()

    print("\n" + "=" * 80)
    print("🏁 AGILE SPRINT FLOW EXECUTION FINISHED")
    print("=" * 80)

    if isinstance(result, SprintReleasePackage):
        _display_and_export_artifacts(result, iterations=flow.state.iteration_count)
    elif flow.state.release_package:
        _display_and_export_artifacts(flow.state.release_package, iterations=flow.state.iteration_count)
    else:
        print("Flow Result:", result)


def run() -> None:
    """Executes the standard linear sequential Crew pipeline."""
    load_dotenv()
    os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

    inputs = {"project_requirements": SAMPLE_REQUIREMENTS}

    print("=" * 80)
    print("🚀 INITIALIZING AGILE DEV CREW: LINEAR SPRINT EXECUTION")
    print("=" * 80)

    crew_instance = AgileDevCrew()
    crew_runner = crew_instance.crew()
    result = crew_runner.kickoff(inputs=inputs)

    print("\n" + "=" * 80)
    print("🏁 LINEAR SPRINT PIPELINE COMPLETE")
    print("=" * 80)

    if hasattr(result, "pydantic") and isinstance(result.pydantic, SprintReleasePackage):
        _display_and_export_artifacts(result.pydantic, iterations=0)
    else:
        print("Raw Task Output:")
        print(result.raw if hasattr(result, "raw") else str(result))


def _display_and_export_artifacts(release: SprintReleasePackage, iterations: int = 0) -> None:
    """Renders the executive sprint review and saves deployment assets to disk."""
    print(f"\n📦 RELEASE VERSION: {release.release_version}")
    print(f"🎯 SPRINT GOAL: {release.sprint_goal}")
    print(f"🔄 REWORK CYCLES COMPLETED: {iterations}")
    print(f"📊 RELEASE READINESS SCORE: {release.release_readiness_score}/100.0")
    print(f"✅ RELEASE SIGNOFF: {'APPROVED FOR PRODUCTION' if release.release_signoff else 'BLOCKED'}")

    print("\n--- SPRINT REVIEW SUMMARY ---")
    print(release.sprint_review_summary)

    print("\n--- RETROSPECTIVE OBSERVATIONS (KAIZEN) ---")
    for idx, obs in enumerate(release.retrospective_observations, start=1):
        print(f"  {idx}. {obs}")

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
    if len(sys.argv) > 1 and sys.argv[1] == "--linear":
        run()
    else:
        run_flow()
