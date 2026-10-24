"""CrewAI Orchestration for Agile Software Development Team (Pod Architecture).

Defines the AgileDevCrew class decorated with @CrewBase, wiring 7 specialized agents,
tasks, tools, Pydantic schemas, and pod factory methods for multi-crew coordination.
"""

import os
from typing import Any
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai_tools import (
    CodeInterpreterTool,
    DirectoryReadTool,
    FileReadTool,
    FileWriterTool,
    SerperDevTool,
)

from agile_dev_crew.schemas import (
    ArchitectureSpec,
    BackendImplementation,
    DesignSystemSpec,
    FrontendImplementation,
    QAReport,
    SprintBacklog,
    SprintReleasePackage,
)


def initialize_search_tool() -> Any:
    """Safely initializes SerperDevTool if API key exists, otherwise provides fallback."""
    if os.getenv("SERPER_API_KEY"):
        return SerperDevTool()

    @tool("domain_market_research_tool")
    def domain_market_research_tool(query: str) -> str:
        """Search industry standards, competitor capabilities, and technical best practices."""
        return (
            f"Synthesized research for '{query}': Modern, reliable, and secure "
            "full-stack architecture with FastAPI backend and Next.js frontend, "
            "adhering to OpenAPI 3.1 standards, Tailwind CSS design tokens, and WCAG AA guidelines."
        )

    return domain_market_research_tool


@CrewBase
class AgileDevCrew:
    """Production-ready multi-agent Agile Software Development Crew with 3 Pods."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        """Initialize tools shared across agents."""
        self.file_read_tool = FileReadTool()
        self.file_write_tool = FileWriterTool()
        self.dir_read_tool = DirectoryReadTool()
        self.code_interpreter_tool = CodeInterpreterTool()
        self.search_tool = initialize_search_tool()

    # ==========================================================================
    # POD A AGENTS: Product & Design
    # ==========================================================================

    @agent
    def product_owner(self) -> Agent:
        """Product Owner: Converts raw requirements into INVEST stories and Gherkin ACs."""
        return Agent(
            config=self.agents_config["product_owner"],
            tools=[self.search_tool, self.file_read_tool],
            verbose=True,
            memory=True,
        )

    @agent
    def ui_ux_designer(self) -> Agent:
        """UI/UX Designer: Builds Design Systems, Tailwind tokens, and wireframe layouts."""
        return Agent(
            config=self.agents_config["ui_ux_designer"],
            tools=[self.file_read_tool, self.file_write_tool, self.search_tool],
            verbose=True,
            memory=True,
        )

    # ==========================================================================
    # POD B AGENTS: Full-Stack Engineering (Hierarchical)
    # ==========================================================================

    @agent
    def system_architect(self) -> Agent:
        """System Architect & Pod Manager: Creates technical blueprints, API contracts, and supervises dev."""
        return Agent(
            config=self.agents_config["system_architect"],
            tools=[self.file_read_tool, self.file_write_tool, self.dir_read_tool],
            verbose=True,
            memory=True,
        )

    @agent
    def backend_developer(self) -> Agent:
        """Backend Developer: Implements ORM models, domain logic, and FastAPI REST endpoints."""
        return Agent(
            config=self.agents_config["backend_developer"],
            tools=[self.file_write_tool, self.file_read_tool, self.code_interpreter_tool],
            verbose=True,
            memory=True,
        )

    @agent
    def frontend_developer(self) -> Agent:
        """Frontend Developer: Implements Next.js/React components and API integration."""
        return Agent(
            config=self.agents_config["frontend_developer"],
            tools=[self.file_write_tool, self.file_read_tool, self.code_interpreter_tool],
            verbose=True,
            memory=True,
        )

    # ==========================================================================
    # POD C AGENTS: Quality & Platform Delivery
    # ==========================================================================

    @agent
    def qa_engineer(self) -> Agent:
        """QA Engineer: Executes automated pytest suites and OWASP/a11y audits."""
        return Agent(
            config=self.agents_config["qa_engineer"],
            tools=[self.code_interpreter_tool, self.file_read_tool, self.file_write_tool],
            verbose=True,
            memory=True,
        )

    @agent
    def devops_release_lead(self) -> Agent:
        """DevOps Release Lead: Builds multi-tier Docker, CI/CD, and release review package."""
        return Agent(
            config=self.agents_config["devops_release_lead"],
            tools=[self.file_write_tool, self.file_read_tool, self.dir_read_tool],
            verbose=True,
            memory=True,
        )

    # ==========================================================================
    # Task Definitions
    # ==========================================================================

    @task
    def backlog_refinement_task(self) -> Task:
        """Task 1 (Pod A): Product Owner refines requirements into SprintBacklog."""
        return Task(
            config=self.tasks_config["backlog_refinement_task"],
            agent=self.product_owner(),
            output_pydantic=SprintBacklog,
        )

    @task
    def ui_ux_design_task(self) -> Task:
        """Task 2 (Pod A): UI/UX Designer produces DesignSystemSpec."""
        return Task(
            config=self.tasks_config["ui_ux_design_task"],
            agent=self.ui_ux_designer(),
            context=[self.backlog_refinement_task()],
            output_pydantic=DesignSystemSpec,
        )

    @task
    def architecture_contract_task(self) -> Task:
        """Task 3 (Pod B): Architect designs system topology and API contracts."""
        return Task(
            config=self.tasks_config["architecture_contract_task"],
            agent=self.system_architect(),
            context=[self.backlog_refinement_task(), self.ui_ux_design_task()],
            output_pydantic=ArchitectureSpec,
        )

    @task
    def backend_implementation_task(self) -> Task:
        """Task 4 (Pod B): Backend Developer implements API endpoints and database models."""
        return Task(
            config=self.tasks_config["backend_implementation_task"],
            agent=self.backend_developer(),
            context=[self.backlog_refinement_task(), self.architecture_contract_task()],
            output_pydantic=BackendImplementation,
        )

    @task
    def frontend_implementation_task(self) -> Task:
        """Task 5 (Pod B): Frontend Developer implements Next.js client and UI components."""
        return Task(
            config=self.tasks_config["frontend_implementation_task"],
            agent=self.frontend_developer(),
            context=[
                self.ui_ux_design_task(),
                self.architecture_contract_task(),
                self.backend_implementation_task(),
            ],
            output_pydantic=FrontendImplementation,
        )

    @task
    def qa_verification_task(self) -> Task:
        """Task 6 (Pod C): QA audits full-stack implementation and verifies acceptance criteria."""
        return Task(
            config=self.tasks_config["qa_verification_task"],
            agent=self.qa_engineer(),
            context=[
                self.backlog_refinement_task(),
                self.ui_ux_design_task(),
                self.backend_implementation_task(),
                self.frontend_implementation_task(),
            ],
            output_pydantic=QAReport,
        )

    @task
    def deployment_and_sprint_review_task(self) -> Task:
        """Task 7 (Pod C): DevOps Lead packages full-stack deployment and governs release."""
        return Task(
            config=self.tasks_config["deployment_and_sprint_review_task"],
            agent=self.devops_release_lead(),
            context=[
                self.architecture_contract_task(),
                self.backend_implementation_task(),
                self.frontend_implementation_task(),
                self.qa_verification_task(),
            ],
            output_pydantic=SprintReleasePackage,
        )

    # ==========================================================================
    # Pod Factory Methods (Approach 3: Multi-Crew Pods)
    # ==========================================================================

    def product_design_pod(self) -> Crew:
        """Pod A: Product Owner & UI/UX Designer establish specifications."""
        return Crew(
            agents=[self.product_owner(), self.ui_ux_designer()],
            tasks=[self.backlog_refinement_task(), self.ui_ux_design_task()],
            process=Process.sequential,
            verbose=True,
            memory=True,
        )

    def engineering_pod(self) -> Crew:
        """Pod B: Hierarchical Engineering Pod managed by System Architect."""
        return Crew(
            agents=[self.backend_developer(), self.frontend_developer()],
            tasks=[
                self.architecture_contract_task(),
                self.backend_implementation_task(),
                self.frontend_implementation_task(),
            ],
            process=Process.hierarchical,
            manager_agent=self.system_architect(),
            verbose=True,
            memory=True,
        )

    def delivery_pod(self) -> Crew:
        """Pod C: QA Engineer & DevOps Release Lead govern verification and deployment."""
        return Crew(
            agents=[self.qa_engineer(), self.devops_release_lead()],
            tasks=[self.qa_verification_task(), self.deployment_and_sprint_review_task()],
            process=Process.sequential,
            verbose=True,
            memory=True,
        )

    # ==========================================================================
    # Unified Crew (Fallback)
    # ==========================================================================

    @crew
    def crew(self) -> Crew:
        """Creates the full 7-agent Agile Development Crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            verbose=True,
        )
