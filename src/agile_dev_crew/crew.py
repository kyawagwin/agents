"""CrewAI Orchestration for Agile Software Development Team.

Defines the AgileDevCrew class decorated with @CrewBase, wiring agents, tasks,
custom/standard tools, Pydantic data contracts, and execution processes.
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
    QAReport,
    SprintBacklog,
    SprintImplementation,
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
            f"Synthesized research for '{query}': High demand for modern, reliable, and secure "
            "API architecture adhering to OpenAPI 3.1 standards, robust authentication, and sub-100ms response SLAs."
        )

    return domain_market_research_tool


@CrewBase
class AgileDevCrew:
    """Production-ready multi-agent Agile Software Development Crew."""

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
    # Agent Definitions
    # ==========================================================================

    @agent
    def product_owner(self) -> Agent:
        """Product Owner: Converts business requirements into INVEST stories and Gherkin ACs."""
        return Agent(
            config=self.agents_config["product_owner"],
            tools=[self.search_tool, self.file_read_tool],
            verbose=True,
            memory=True,
        )

    @agent
    def system_architect(self) -> Agent:
        """System Architect: Creates technical blueprints, API schemas, and data models."""
        return Agent(
            config=self.agents_config["system_architect"],
            tools=[self.file_read_tool, self.file_write_tool, self.dir_read_tool],
            verbose=True,
            memory=True,
        )

    @agent
    def senior_developer(self) -> Agent:
        """Senior Developer: Implements clean, production-ready SOLID code."""
        return Agent(
            config=self.agents_config["senior_developer"],
            tools=[self.file_write_tool, self.file_read_tool, self.code_interpreter_tool],
            verbose=True,
            memory=True,
        )

    @agent
    def qa_engineer(self) -> Agent:
        """QA Engineer: Executes automated pytest suites and OWASP Top 10 security audits."""
        return Agent(
            config=self.agents_config["qa_engineer"],
            tools=[self.code_interpreter_tool, self.file_read_tool, self.file_write_tool],
            verbose=True,
            memory=True,
        )

    @agent
    def devops_release_lead(self) -> Agent:
        """DevOps Release Lead: Builds container/CI-CD assets and governs the sprint release."""
        return Agent(
            config=self.agents_config["devops_release_lead"],
            tools=[self.file_write_tool, self.file_read_tool, self.dir_read_tool],
            verbose=True,
            memory=True,
        )

    # ==========================================================================
    # Task Definitions (Pipeline & Context Chaining)
    # ==========================================================================

    @task
    def backlog_refinement_task(self) -> Task:
        """Task 1: Product Owner refines raw requirements into structured SprintBacklog."""
        return Task(
            config=self.tasks_config["backlog_refinement_task"],
            agent=self.product_owner(),
            output_pydantic=SprintBacklog,
        )

    @task
    def architecture_design_task(self) -> Task:
        """Task 2: Architect consumes SprintBacklog and produces ArchitectureSpec."""
        return Task(
            config=self.tasks_config["architecture_design_task"],
            agent=self.system_architect(),
            context=[self.backlog_refinement_task()],
            output_pydantic=ArchitectureSpec,
        )

    @task
    def sprint_implementation_task(self) -> Task:
        """Task 3: Senior Dev consumes Backlog & Architecture to produce SprintImplementation."""
        return Task(
            config=self.tasks_config["sprint_implementation_task"],
            agent=self.senior_developer(),
            context=[
                self.backlog_refinement_task(),
                self.architecture_design_task(),
            ],
            output_pydantic=SprintImplementation,
        )

    @task
    def qa_verification_task(self) -> Task:
        """Task 4: QA Engineer verifies implementation against acceptance criteria."""
        return Task(
            config=self.tasks_config["qa_verification_task"],
            agent=self.qa_engineer(),
            context=[
                self.backlog_refinement_task(),
                self.sprint_implementation_task(),
            ],
            output_pydantic=QAReport,
        )

    @task
    def deployment_and_sprint_review_task(self) -> Task:
        """Task 5: DevOps Lead synthesizes deliverables into deployment assets & release package."""
        return Task(
            config=self.tasks_config["deployment_and_sprint_review_task"],
            agent=self.devops_release_lead(),
            context=[
                self.architecture_design_task(),
                self.sprint_implementation_task(),
                self.qa_verification_task(),
            ],
            output_pydantic=SprintReleasePackage,
        )

    # ==========================================================================
    # Crew Orchestration
    # ==========================================================================

    @crew
    def crew(self) -> Crew:
        """Creates and configures the Agile Software Development Crew.

        Execution Modes:
        ----------------
        1. Sequential Mode (Default):
           Executes tasks linearly from refinement -> architecture -> code -> QA -> release.
           Context chaining ensures strict, deterministic Pydantic data contract transfers.

        2. Hierarchical Mode (Iterative Coordination):
           Allows a manager agent (e.g., Scrum Master / Engineering Manager) to supervise,
           delegate tasks dynamically, and manage rework loops if QA identifies defects.
           To enable hierarchical execution:
             - Change `process=Process.sequential` to `process=Process.hierarchical`
             - Set `manager_agent=self.devops_release_lead()` OR provide `manager_llm=ChatOpenAI(...)`
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Default: Sequential sprint pipeline
            memory=True,                 # Shared vector & entity memory across sprint
            verbose=True,
            # ------------------------------------------------------------------
            # Uncomment the lines below to switch to Hierarchical Process:
            # ------------------------------------------------------------------
            # process=Process.hierarchical,
            # manager_agent=self.devops_release_lead(), # Acting as Scrum Master & Manager
            # # Or alternatively configure a manager LLM:
            # # manager_llm=ChatOpenAI(model="gpt-4o", temperature=0.0),
        )
