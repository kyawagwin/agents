"""CrewAI Flow: Iterative Agile Sprint with Self-Healing QA Rework Loop.

Orchestrates an event-driven workflow using @start, @listen, and @router:
1. @start: Backlog refinement & System architecture.
2. @listen(or_(start, "rework_needed")): Senior Developer initial code or defect remediation.
3. @listen(implement_code): QA Engineer automated test execution & security audit.
4. @router(verify_qa): Evaluates QAReport. If tests fail or defects exist, routes back
   to Senior Developer ("rework_needed") until all tests pass, or transitions to "qa_passed".
5. @listen("qa_passed"): DevOps Release Lead generates deployment assets & sprint review.
6. @listen("max_retries_exceeded"): Gracefully escalates unresolvable defects.
"""

import json
import logging
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from crewai import Crew, Process, Task
from crewai.flow.flow import Flow, listen, or_, router, start

from agile_dev_crew.crew import AgileDevCrew
from agile_dev_crew.schemas import (
    ArchitectureSpec,
    QAReport,
    SprintBacklog,
    SprintImplementation,
    SprintReleasePackage,
)

logger = logging.getLogger("AgileSprintFlow")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SprintFlowState(BaseModel):
    """Persistent state tracking across the iterative sprint flow lifecycle."""

    project_requirements: str = Field(
        default="",
        description="Raw high-level business/technical requirement prompt"
    )
    sprint_backlog: Optional[SprintBacklog] = Field(
        default=None,
        description="Structured backlog produced by the Product Owner"
    )
    architecture_spec: Optional[ArchitectureSpec] = Field(
        default=None,
        description="Technical design blueprint produced by the System Architect"
    )
    sprint_implementation: Optional[SprintImplementation] = Field(
        default=None,
        description="Latest application source code produced by the Senior Developer"
    )
    qa_report: Optional[QAReport] = Field(
        default=None,
        description="Latest QA verification and security audit report"
    )
    release_package: Optional[SprintReleasePackage] = Field(
        default=None,
        description="Final deployment assets and sprint review package"
    )
    iteration_count: int = Field(
        default=0,
        description="Current rework iteration counter between Senior Dev and QA"
    )
    max_iterations: int = Field(
        default=3,
        description="Circuit-breaker limit on remediation loops to prevent infinite cycles"
    )
    rework_history: List[str] = Field(
        default_factory=list,
        description="Audit log of rework notes and defect remediation summaries"
    )


class AgileSprintFlow(Flow[SprintFlowState]):
    """Event-driven Agile Sprint workflow with an autonomous QA feedback rework loop."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.crew_base = AgileDevCrew()

    # ==========================================================================
    # Phase 1: Sprint Initiation & Architecture
    # ==========================================================================

    @start()
    def plan_and_architect(self) -> str:
        """Phase 1: Product Owner refines backlog; System Architect designs blueprint."""
        logger.info("🎬 [FLOW START] Initiating Agile Backlog Refinement & System Architecture...")

        product_owner_agent = self.crew_base.product_owner()
        system_architect_agent = self.crew_base.system_architect()

        # Task 1: Backlog Refinement
        refinement_task = Task(
            config=self.crew_base.tasks_config["backlog_refinement_task"],
            agent=product_owner_agent,
            output_pydantic=SprintBacklog,
        )

        # Task 2: Architecture Design (depends on refinement)
        arch_task = Task(
            config=self.crew_base.tasks_config["architecture_design_task"],
            agent=system_architect_agent,
            context=[refinement_task],
            output_pydantic=ArchitectureSpec,
        )

        planning_crew = Crew(
            agents=[product_owner_agent, system_architect_agent],
            tasks=[refinement_task, arch_task],
            process=Process.sequential,
            verbose=True,
        )

        planning_crew.kickoff(
            inputs={"project_requirements": self.state.project_requirements}
        )

        self.state.sprint_backlog = refinement_task.output.pydantic
        self.state.architecture_spec = arch_task.output.pydantic

        logger.info(
            f"✅ [PLANNING COMPLETE] Sprint Goal: '{self.state.sprint_backlog.sprint_goal}' | "
            f"Committed Points: {self.state.sprint_backlog.total_story_points}"
        )
        return "planning_complete"

    # ==========================================================================
    # Phase 2: Implementation & Rework Loop
    # ==========================================================================

    @listen(or_(plan_and_architect, "rework_needed"))
    def implement_code(self) -> str:
        """Phase 2: Senior Developer writes initial code or fixes defects identified by QA."""
        senior_dev = self.crew_base.senior_developer()

        if self.state.iteration_count == 0:
            logger.info("💻 [DEV PHASE] Senior Developer generating initial production codebase...")
            dev_task = Task(
                config=self.crew_base.tasks_config["sprint_implementation_task"],
                agent=senior_dev,
                output_pydantic=SprintImplementation,
            )
            context_inputs = {
                "project_requirements": self.state.project_requirements,
                "sprint_backlog": self.state.sprint_backlog.model_dump_json(indent=2),
                "architecture_spec": self.state.architecture_spec.model_dump_json(indent=2),
            }
        else:
            logger.warning(
                f"🔧 [REWORK LOOP #{self.state.iteration_count}] Senior Developer remediating QA defects..."
            )
            # Extract failed tests and defects for targeted remediation
            failed_tests = [
                tc.model_dump()
                for tc in self.state.qa_report.test_cases
                if tc.status == "FAILED"
            ]
            defects = [d.model_dump() for d in self.state.qa_report.defects]

            rework_prompt = (
                f"REWORK ITERATION #{self.state.iteration_count} - CRITICAL DEFECT REMEDIATION:\n\n"
                f"QA Sign-Off Status: {self.state.qa_report.sign_off_status}\n"
                f"Failed Tests ({len(failed_tests)}):\n"
                f"{json.dumps(failed_tests, indent=2)}\n\n"
                f"Identified Defects ({len(defects)}):\n"
                f"{json.dumps(defects, indent=2)}\n\n"
                f"QA Commentary:\n{self.state.qa_report.qa_notes}\n\n"
                f"CURRENT IMPLEMENTATION TO FIX:\n"
                f"{self.state.sprint_implementation.model_dump_json(indent=2)}\n\n"
                f"MANDATORY REMEDIATION DIRECTIVES:\n"
                f"1. Fix the root causes for every single failing test listed above.\n"
                f"2. Resolve all reported defects (boundary handling, validation, logic, or security).\n"
                f"3. Preserve all existing working functionality (zero regression).\n"
                f"4. Provide the complete, updated source files in the SprintImplementation schema."
            )

            dev_task = Task(
                description=rework_prompt,
                expected_output=(
                    "A fully updated SprintImplementation object with all defects rectified, "
                    "failing tests accommodated, and unabridged production source files."
                ),
                agent=senior_dev,
                output_pydantic=SprintImplementation,
            )
            context_inputs = {}

        dev_crew = Crew(
            agents=[senior_dev],
            tasks=[dev_task],
            verbose=True,
        )
        dev_crew.kickoff(inputs=context_inputs)
        self.state.sprint_implementation = dev_task.output.pydantic

        logger.info(
            f"📦 [DEV DELIVERED] Codebase updated with {len(self.state.sprint_implementation.files)} files."
        )
        return "code_implemented"

    # ==========================================================================
    # Phase 3: QA Verification & Automated Testing
    # ==========================================================================

    @listen(implement_code)
    def verify_qa(self) -> str:
        """Phase 3: QA Engineer audits code, executes pytest suites, and checks OWASP compliance."""
        logger.info(
            f"🧪 [QA AUDIT #{self.state.iteration_count}] QA Engineer running verification test suites..."
        )

        qa_engineer = self.crew_base.qa_engineer()

        qa_task = Task(
            description=(
                f"Perform exhaustive Quality Assurance and Security Verification on the latest implementation.\n\n"
                f"Sprint Backlog Acceptance Criteria:\n"
                f"{self.state.sprint_backlog.model_dump_json(indent=2)}\n\n"
                f"Codebase Under Test:\n"
                f"{self.state.sprint_implementation.model_dump_json(indent=2)}\n\n"
                f"Verification Directives:\n"
                f"1. Validate every Gherkin scenario defined in the user stories.\n"
                f"2. Execute unit, integration, and security test suites.\n"
                f"3. Check for edge cases, null handling, and OWASP Top 10 vulnerabilities.\n"
                f"4. Set 'sign_off_status' to 'APPROVED' ONLY if total failed_tests == 0 and no HIGH/CRITICAL defects exist.\n"
                f"   Otherwise set to 'REJECTED' or 'APPROVED_WITH_CONDITIONS'."
            ),
            expected_output=(
                "A complete QAReport object with test execution details, defect tracking, "
                "OWASP security audit, and formal sign_off_status."
            ),
            agent=qa_engineer,
            output_pydantic=QAReport,
        )

        qa_crew = Crew(
            agents=[qa_engineer],
            tasks=[qa_task],
            verbose=True,
        )
        qa_crew.kickoff()
        self.state.qa_report = qa_task.output.pydantic

        logger.info(
            f"📊 [QA RESULTS] Status: {self.state.qa_report.sign_off_status} | "
            f"Passed: {self.state.qa_report.passed_tests} | "
            f"Failed: {self.state.qa_report.failed_tests} | "
            f"Defects: {len(self.state.qa_report.defects)}"
        )
        return "qa_verified"

    # ==========================================================================
    # Phase 4: Dynamic Router (The Feedback Loop Engine)
    # ==========================================================================

    @router(verify_qa)
    def evaluate_qa_results(self) -> str:
        """Phase 4 Router: Evaluates QA report and routes back to Dev or proceeds to Release.

        Routing Logic:
        --------------
        - If sign_off_status == 'APPROVED' and failed_tests == 0:
            -> Route to 'qa_passed' (Release Lead builds deployment package).
        - If tests failed or defects discovered:
            - If iteration_count < max_iterations:
                -> Increment iteration_count and route to 'rework_needed' (triggers Senior Dev).
            - If iteration_count >= max_iterations:
                -> Route to 'max_retries_exceeded' (circuit breaker prevents infinite loop).
        """
        qa = self.state.qa_report

        # Happy Path: 100% tests passed and formal approval granted
        if qa.sign_off_status == "APPROVED" and qa.failed_tests == 0:
            logger.info("🎉 [ROUTER] QA Sign-Off APPROVED with 0 failures! Routing to deployment...")
            return "qa_passed"

        # Circuit Breaker: Prevent infinite loop if defects cannot be resolved autonomously
        if self.state.iteration_count >= self.state.max_iterations:
            logger.error(
                f"🛑 [ROUTER] Max rework iterations ({self.state.max_iterations}) exceeded. "
                "Routing to escalation handler..."
            )
            return "max_retries_exceeded"

        # Rework Required: Feed defect report back into Senior Developer
        self.state.iteration_count += 1
        rework_summary = (
            f"Iteration {self.state.iteration_count}: {qa.failed_tests} failed test(s), "
            f"{len(qa.defects)} defect(s). Reason: {qa.qa_notes}"
        )
        self.state.rework_history.append(rework_summary)

        logger.warning(
            f"🔁 [ROUTER] QA Verification FAILED (Iteration {self.state.iteration_count}/"
            f"{self.state.max_iterations}). Routing failed report back to Senior Developer..."
        )
        return "rework_needed"

    # ==========================================================================
    # Phase 5: Deployment & Release or Escalation
    # ==========================================================================

    @listen("qa_passed")
    def finalize_deployment(self) -> SprintReleasePackage:
        """Phase 5A: DevOps Lead generates container, CI/CD, and release review package."""
        logger.info("🚀 [RELEASE] QA sign-off confirmed. DevOps Lead finalizing release package...")

        devops_agent = self.crew_base.devops_release_lead()

        release_task = Task(
            description=(
                f"Compile the production deployment assets and Sprint Review package.\n\n"
                f"Sprint Goal: {self.state.sprint_backlog.sprint_goal}\n"
                f"Rework Cycles Completed: {self.state.iteration_count}\n"
                f"Final QA Test Pass Rate: {self.state.qa_report.passed_tests}/"
                f"{self.state.qa_report.total_tests}\n"
                f"Coverage: {self.state.qa_report.code_coverage_percentage}%\n\n"
                f"Architecture Spec:\n{self.state.architecture_spec.model_dump_json(indent=2)}\n\n"
                f"Verified Codebase:\n{self.state.sprint_implementation.model_dump_json(indent=2)}\n\n"
                f"Generate production Dockerfile, docker-compose.yml, GitHub Actions CI/CD workflow, "
                f"calculate release readiness score, and compile the final sprint review summary."
            ),
            expected_output=(
                "A complete SprintReleasePackage object with container files, CI/CD YAML, "
                "and Sprint Review notes."
            ),
            agent=devops_agent,
            output_pydantic=SprintReleasePackage,
        )

        devops_crew = Crew(
            agents=[devops_agent],
            tasks=[release_task],
            verbose=True,
        )
        devops_crew.kickoff()
        self.state.release_package = release_task.output.pydantic

        logger.info(
            f"🏁 [SPRINT RELEASE READY] Version: {self.state.release_package.release_version} | "
            f"Readiness Score: {self.state.release_package.release_readiness_score}/100.0"
        )
        return self.state.release_package

    @listen("max_retries_exceeded")
    def handle_blocked_sprint(self) -> dict:
        """Phase 5B: Circuit breaker handler documenting blocking defects for human review."""
        logger.critical(
            "🚨 [ESCALATION] Sprint execution halted: Unresolved defects persist after "
            f"{self.state.max_iterations} remediation cycles."
        )
        escalation_report = {
            "status": "BLOCKED_AWAITING_HUMAN_TRIAGE",
            "iterations_attempted": self.state.iteration_count,
            "failed_tests_count": self.state.qa_report.failed_tests,
            "defects_summary": [d.model_dump() for d in self.state.qa_report.defects],
            "rework_history": self.state.rework_history,
            "remediation_recommendation": (
                "Human engineering lead required to inspect architecture constraints "
                "or re-scope acceptance criteria."
            ),
        }
        return escalation_report
