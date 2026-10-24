"""CrewAI Flow: Hierarchical Cross-Functional Pod Orchestration (Approach 3).

Coordinates 3 specialized engineering pods:
- Pod A: Product & Design Pod (Product Owner + UI/UX Designer)
- Pod B: Full-Stack Engineering Pod (System Architect Manager + Backend & Frontend Developers)
- Pod C: Quality & Platform Delivery Pod (QA Engineer + DevOps Release Lead)

Includes an event-driven self-healing QA rework loop routing defects back to Pod B
under the supervision of the System Architect until all tests pass.
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
    BackendImplementation,
    DesignSystemSpec,
    FrontendImplementation,
    QAReport,
    SprintBacklog,
    SprintReleasePackage,
)

logger = logging.getLogger("HierarchicalPodSprintFlow")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class PodSprintFlowState(BaseModel):
    """Persistent state tracking across the multi-pod sprint lifecycle."""

    project_requirements: str = Field(
        default="",
        description="Raw high-level business and technical requirement prompt"
    )
    sprint_backlog: Optional[SprintBacklog] = Field(
        default=None,
        description="Structured backlog and Gherkin criteria from Product Owner (Pod A)"
    )
    design_system: Optional[DesignSystemSpec] = Field(
        default=None,
        description="UI tokens, components, and wireframes from UI/UX Designer (Pod A)"
    )
    architecture_spec: Optional[ArchitectureSpec] = Field(
        default=None,
        description="API contracts and system topology from System Architect (Pod B)"
    )
    backend_implementation: Optional[BackendImplementation] = Field(
        default=None,
        description="Backend services, ORM models, and routes from Backend Dev (Pod B)"
    )
    frontend_implementation: Optional[FrontendImplementation] = Field(
        default=None,
        description="Client components, views, and hooks from Frontend Dev (Pod B)"
    )
    qa_report: Optional[QAReport] = Field(
        default=None,
        description="QA verification and security audit report from QA Engineer (Pod C)"
    )
    release_package: Optional[SprintReleasePackage] = Field(
        default=None,
        description="Production container and CI/CD assets from DevOps Lead (Pod C)"
    )
    iteration_count: int = Field(
        default=0,
        description="Number of rework cycles between QA (Pod C) and Engineering (Pod B)"
    )
    max_iterations: int = Field(
        default=3,
        description="Circuit-breaker threshold on rework iterations"
    )
    rework_history: List[str] = Field(
        default_factory=list,
        description="Audit log of rework notes and defect remediation summaries"
    )


class HierarchicalPodSprintFlow(Flow[PodSprintFlowState]):
    """Orchestrates 3 cross-functional pods with hierarchical engineering and QA rework."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.crew_base = AgileDevCrew()

    # ==========================================================================
    # POD A: Product & Design Pod (PO + UI/UX Designer)
    # ==========================================================================

    @start()
    def run_product_design_pod(self) -> str:
        """Pod A: Product Owner establishes backlog; UI/UX Designer builds Design System."""
        logger.info("🎨 [POD A: PRODUCT & DESIGN] Starting Backlog Refinement & UI/UX Design...")

        po_agent = self.crew_base.product_owner()
        designer_agent = self.crew_base.ui_ux_designer()

        refinement_task = Task(
            config=self.crew_base.tasks_config["backlog_refinement_task"],
            agent=po_agent,
            output_pydantic=SprintBacklog,
        )

        design_task = Task(
            config=self.crew_base.tasks_config["ui_ux_design_task"],
            agent=designer_agent,
            context=[refinement_task],
            output_pydantic=DesignSystemSpec,
        )

        pod_a = Crew(
            agents=[po_agent, designer_agent],
            tasks=[refinement_task, design_task],
            process=Process.sequential,
            verbose=True,
            memory=True,
        )

        pod_a.kickoff(inputs={"project_requirements": self.state.project_requirements})

        self.state.sprint_backlog = refinement_task.output.pydantic
        self.state.design_system = design_task.output.pydantic

        logger.info(
            f"✅ [POD A COMPLETE] Sprint Goal: '{self.state.sprint_backlog.sprint_goal}' | "
            f"Components Defined: {len(self.state.design_system.components)} | "
            f"Wireframes: {len(self.state.design_system.layouts)}"
        )
        return "specs_ready"

    # ==========================================================================
    # POD B: Full-Stack Engineering Pod (Architect Manager + Backend & Frontend)
    # ==========================================================================

    @listen(or_(run_product_design_pod, "rework_needed"))
    def run_engineering_pod(self) -> str:
        """Pod B: System Architect directs Backend and Frontend developers in hierarchical mode."""
        architect = self.crew_base.system_architect()
        backend_dev = self.crew_base.backend_developer()
        frontend_dev = self.crew_base.frontend_developer()

        if self.state.iteration_count == 0:
            logger.info("⚙️ [POD B: ENGINEERING] Initiating Full-Stack Implementation...")

            arch_task = Task(
                config=self.crew_base.tasks_config["architecture_contract_task"],
                agent=architect,
                output_pydantic=ArchitectureSpec,
            )

            backend_task = Task(
                config=self.crew_base.tasks_config["backend_implementation_task"],
                agent=backend_dev,
                context=[arch_task],
                output_pydantic=BackendImplementation,
            )

            frontend_task = Task(
                config=self.crew_base.tasks_config["frontend_implementation_task"],
                agent=frontend_dev,
                context=[arch_task, backend_task],
                output_pydantic=FrontendImplementation,
            )

            pod_b = Crew(
                agents=[backend_dev, frontend_dev],
                tasks=[arch_task, backend_task, frontend_task],
                process=Process.hierarchical,
                manager_agent=architect,
                verbose=True,
                memory=True,
            )

            context_inputs = {
                "project_requirements": self.state.project_requirements,
                "sprint_backlog": self.state.sprint_backlog.model_dump_json(indent=2),
                "design_system": self.state.design_system.model_dump_json(indent=2),
            }
            pod_b.kickoff(inputs=context_inputs)

            self.state.architecture_spec = arch_task.output.pydantic
            self.state.backend_implementation = backend_task.output.pydantic
            self.state.frontend_implementation = frontend_task.output.pydantic

        else:
            logger.warning(
                f"🔧 [POD B: REWORK LOOP #{self.state.iteration_count}] Architect delegating defect fixes..."
            )
            # Separate defects by tier for targeted remediation
            backend_defects = [
                d.model_dump()
                for d in self.state.qa_report.defects
                if d.target_tier in ("backend", "architecture")
            ]
            frontend_defects = [
                d.model_dump()
                for d in self.state.qa_report.defects
                if d.target_tier in ("frontend", "ui_ux")
            ]

            rework_prompt = (
                f"ENGINEERING POD REMEDIATION (Iteration #{self.state.iteration_count}):\n\n"
                f"QA Sign-Off Status: {self.state.qa_report.sign_off_status}\n"
                f"Total Failed Tests: {self.state.qa_report.failed_tests}\n\n"
                f"BACKEND DEFECTS TO FIX ({len(backend_defects)}):\n"
                f"{json.dumps(backend_defects, indent=2)}\n\n"
                f"FRONTEND DEFECTS TO FIX ({len(frontend_defects)}):\n"
                f"{json.dumps(frontend_defects, indent=2)}\n\n"
                f"QA AUDIT COMMENTARY:\n{self.state.qa_report.qa_notes}\n\n"
                f"DIRECTIVES FOR SYSTEM ARCHITECT & DEVELOPERS:\n"
                f"1. Architect: Coordinate fix across tiers, preserving contract alignment.\n"
                f"2. Backend Dev: Patch route errors, validation, or database logic.\n"
                f"3. Frontend Dev: Resolve UI state mismatches, a11y contrast, or styling bugs.\n"
                f"4. Deliver updated BackendImplementation and FrontendImplementation."
            )

            backend_rework_task = Task(
                description=f"{rework_prompt}\n\nDeliver updated BackendImplementation.",
                expected_output="An updated BackendImplementation with all backend defects resolved.",
                agent=backend_dev,
                output_pydantic=BackendImplementation,
            )

            frontend_rework_task = Task(
                description=f"{rework_prompt}\n\nDeliver updated FrontendImplementation.",
                expected_output="An updated FrontendImplementation with all frontend defects resolved.",
                agent=frontend_dev,
                output_pydantic=FrontendImplementation,
            )

            pod_b = Crew(
                agents=[backend_dev, frontend_dev],
                tasks=[backend_rework_task, frontend_rework_task],
                process=Process.hierarchical,
                manager_agent=architect,
                verbose=True,
                memory=True,
            )
            pod_b.kickoff()

            self.state.backend_implementation = backend_rework_task.output.pydantic
            self.state.frontend_implementation = frontend_rework_task.output.pydantic

        logger.info(
            f"📦 [POD B DELIVERED] Backend: "
            f"{len(self.state.backend_implementation.api_endpoints_and_routers)} routes, "
            f"{len(self.state.backend_implementation.orm_and_db_models)} models | "
            f"Frontend: {len(self.state.frontend_implementation.ui_components)} components, "
            f"{len(self.state.frontend_implementation.pages_and_views)} views"
        )
        return "engineering_complete"

    # ==========================================================================
    # POD C: Quality & Platform Delivery Pod (QA Engineer + DevOps Lead)
    # ==========================================================================

    @listen(run_engineering_pod)
    def run_qa_verification(self) -> str:
        """Pod C: QA Engineer executes full-stack test verification & security/a11y audit."""
        logger.info(
            f"🧪 [POD C: QA AUDIT #{self.state.iteration_count}] Auditing Full-Stack Implementation..."
        )

        qa_agent = self.crew_base.qa_engineer()

        qa_task = Task(
            description=(
                f"Execute thorough QA verification across backend and frontend tiers.\n\n"
                f"Sprint Backlog User Stories & Gherkin ACs:\n"
                f"{self.state.sprint_backlog.model_dump_json(indent=2)}\n\n"
                f"UI/UX Design System Guidelines:\n"
                f"{self.state.design_system.model_dump_json(indent=2)}\n\n"
                f"Backend Implementation:\n"
                f"{self.state.backend_implementation.model_dump_json(indent=2)}\n\n"
                f"Frontend Implementation:\n"
                f"{self.state.frontend_implementation.model_dump_json(indent=2)}\n\n"
                f"Verification Directives:\n"
                f"1. Verify all Gherkin acceptance criteria.\n"
                f"2. Audit backend APIs for OWASP Top 10 vulnerabilities.\n"
                f"3. Audit frontend components for WCAG 2.1 AA accessibility (contrast, ARIA).\n"
                f"4. Tag every defect with its target_tier ('backend', 'frontend', 'architecture', 'ui_ux').\n"
                f"5. Issue sign_off_status = 'APPROVED' ONLY if failed_tests == 0 and no HIGH/CRITICAL defects exist."
            ),
            expected_output="A complete QAReport object evaluating the full-stack system.",
            agent=qa_agent,
            output_pydantic=QAReport,
        )

        qa_crew = Crew(
            agents=[qa_agent],
            tasks=[qa_task],
            verbose=True,
        )
        qa_crew.kickoff()
        self.state.qa_report = qa_task.output.pydantic

        logger.info(
            f"📊 [POD C: QA REPORT] Status: {self.state.qa_report.sign_off_status} | "
            f"Passed: {self.state.qa_report.passed_tests} | "
            f"Failed: {self.state.qa_report.failed_tests} | "
            f"Defects: {len(self.state.qa_report.defects)}"
        )
        return "qa_verified"

    # ==========================================================================
    # Dynamic Router: Evaluates QA and routes back to Pod B or forwards to Release
    # ==========================================================================

    @router(run_qa_verification)
    def evaluate_qa_results(self) -> str:
        """Routes failed QA reports back to Engineering Pod (Pod B) or proceeds to Deployment."""
        qa = self.state.qa_report

        # Happy Path: 100% tests passed and approved
        if qa.sign_off_status == "APPROVED" and qa.failed_tests == 0:
            logger.info("🎉 [ROUTER] Full-Stack QA Sign-Off APPROVED! Routing to Pod C Release...")
            return "qa_passed"

        # Circuit Breaker: Prevent infinite rework loops
        if self.state.iteration_count >= self.state.max_iterations:
            logger.error(
                f"🛑 [ROUTER] Max rework iterations ({self.state.max_iterations}) reached. "
                "Halting automated loop for human triage..."
            )
            return "max_retries_exceeded"

        # Rework Required: Feed defect report back into Pod B
        self.state.iteration_count += 1
        summary = (
            f"Iteration {self.state.iteration_count}: {qa.failed_tests} failed tests, "
            f"{len(qa.defects)} defects. Notes: {qa.qa_notes}"
        )
        self.state.rework_history.append(summary)

        logger.warning(
            f"🔁 [ROUTER] QA FAILED ({self.state.iteration_count}/{self.state.max_iterations}). "
            "Routing defect report back to Engineering Pod (Pod B)..."
        )
        return "rework_needed"

    # ==========================================================================
    # POD C: Final Release & Delivery
    # ==========================================================================

    @listen("qa_passed")
    def run_delivery_pod(self) -> SprintReleasePackage:
        """Pod C: DevOps Release Lead builds full-stack Docker, CI/CD, and Sprint Review."""
        logger.info("🚀 [POD C: DELIVERY] Finalizing full-stack deployment and Sprint Governance...")

        devops_agent = self.crew_base.devops_release_lead()

        release_task = Task(
            description=(
                f"Compile full-stack containerization assets and Sprint Review package.\n\n"
                f"Sprint Goal: {self.state.sprint_backlog.sprint_goal}\n"
                f"Rework Cycles Completed: {self.state.iteration_count}\n"
                f"Architecture Spec:\n{self.state.architecture_spec.model_dump_json(indent=2)}\n\n"
                f"Backend Modules:\n{self.state.backend_implementation.model_dump_json(indent=2)}\n\n"
                f"Frontend Components:\n{self.state.frontend_implementation.model_dump_json(indent=2)}\n\n"
                f"QA Sign-Off Audit:\n{self.state.qa_report.model_dump_json(indent=2)}\n\n"
                f"Generate:\n"
                f"1. Multi-stage Dockerfile for FastAPI backend.\n"
                f"2. Multi-stage Dockerfile for Next.js frontend.\n"
                f"3. Root docker-compose.yml orchestrating postgres, redis, backend, and frontend.\n"
                f"4. GitHub Actions CI/CD workflow (.github/workflows/pipeline.yml).\n"
                f"5. Calculate composite Release Readiness Score and formulate Sprint Review & Retrospective."
            ),
            expected_output="A complete SprintReleasePackage object ready for production deployment.",
            agent=devops_agent,
            output_pydantic=SprintReleasePackage,
        )

        delivery_crew = Crew(
            agents=[devops_agent],
            tasks=[release_task],
            verbose=True,
        )
        delivery_crew.kickoff()
        self.state.release_package = release_task.output.pydantic

        logger.info(
            f"🏁 [SPRINT RELEASE READY] Version: {self.state.release_package.release_version} | "
            f"Readiness Score: {self.state.release_package.release_readiness_score}/100.0 | "
            f"Signoff: {self.state.release_package.release_signoff}"
        )
        return self.state.release_package

    @listen("max_retries_exceeded")
    def handle_blocked_sprint(self) -> dict:
        """Handles circuit-breaker tripping by compiling an executive escalation report."""
        logger.critical(
            "🚨 [ESCALATION] Sprint execution halted: Blocking defects unresolved after "
            f"{self.state.max_iterations} cycles."
        )
        return {
            "status": "BLOCKED_AWAITING_HUMAN_TRIAGE",
            "iterations_attempted": self.state.iteration_count,
            "failed_tests_count": self.state.qa_report.failed_tests,
            "defects_summary": [d.model_dump() for d in self.state.qa_report.defects],
            "rework_history": self.state.rework_history,
            "remediation_recommendation": (
                "Human engineering manager required to arbitrate API contract drift "
                "or re-scope frontend/backend acceptance criteria."
            ),
        }
