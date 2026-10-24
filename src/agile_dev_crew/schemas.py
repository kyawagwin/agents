"""Pydantic Data Contracts for Agile Dev Crew.

Strict schema definitions enforcing deterministic handoffs across tasks:
1. Product Owner  -> SprintBacklog
2. System Architect -> ArchitectureSpec
3. Senior Developer -> SprintImplementation
4. QA Engineer      -> QAReport
5. DevOps / Scrum   -> SprintReleasePackage
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Phase 1: Product Owner & Backlog Schemas
# ==============================================================================

class AcceptanceCriterion(BaseModel):
    """Gherkin Given-When-Then acceptance criterion scenario."""
    id: str = Field(description="Unique criterion identifier, e.g., 'AC-001'")
    scenario: str = Field(description="Descriptive scenario title")
    given: str = Field(description="Preconditions or system state ('Given...')")
    when: str = Field(description="Action or event triggered ('When...')")
    then: str = Field(description="Observable expected outcome ('Then...')")


class UserStory(BaseModel):
    """INVEST-compliant User Story with Gherkin Acceptance Criteria."""
    id: str = Field(description="Unique story identifier, e.g., 'US-101'")
    title: str = Field(description="Concise, actionable user story title")
    as_a: str = Field(description="Persona requesting the capability ('As a...')")
    i_want: str = Field(description="Desired capability or behavior ('I want...')")
    so_that: str = Field(description="Business value or justification ('So that...')")
    acceptance_criteria: List[AcceptanceCriterion] = Field(
        description="Comprehensive list of Given-When-Then scenarios"
    )
    story_points: int = Field(
        description="Fibonacci estimation value (1, 2, 3, 5, 8, 13)"
    )
    priority: Literal["Must Have", "Should Have", "Could Have", "Won't Have"] = Field(
        description="MoSCoW priority classification"
    )
    technical_notes: Optional[str] = Field(
        default=None,
        description="Edge cases, domain nuances, or architectural prerequisites"
    )


class SprintBacklog(BaseModel):
    """Deterministic output contract for backlog_refinement_task."""
    sprint_goal: str = Field(description="Clear, measurable objective for this sprint")
    definition_of_done: List[str] = Field(
        description="Strict organizational checklist required for story completion"
    )
    user_stories: List[UserStory] = Field(
        description="Prioritized collection of refined user stories"
    )
    total_story_points: int = Field(description="Cumulative story points committed")
    target_velocity: int = Field(description="Expected velocity baseline for the team")


# ==============================================================================
# Phase 2: Architecture & Technical Design Schemas
# ==============================================================================

class DatabaseField(BaseModel):
    """Field definition for relational or document schemas."""
    name: str = Field(description="Column/attribute name")
    type: str = Field(description="Data type (e.g., UUID, VARCHAR(255), TIMESTAMP, INTEGER)")
    primary_key: bool = Field(default=False, description="Whether this field is the primary key")
    nullable: bool = Field(default=False, description="Whether null values are permissible")
    description: Optional[str] = Field(default=None, description="Semantic field documentation")


class DatabaseSchemaModel(BaseModel):
    """Entity-relationship or document data model."""
    table_name: str = Field(description="Entity or table name")
    fields: List[DatabaseField] = Field(description="Schema fields and constraints")
    foreign_keys: List[str] = Field(default_factory=list, description="Foreign key relationships")
    indexes: List[str] = Field(default_factory=list, description="Performance indices")


class ApiEndpoint(BaseModel):
    """REST or OpenAPI endpoint contract."""
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = Field(description="HTTP method")
    path: str = Field(description="Route path with parameters (e.g., '/api/v1/orders/{order_id}')")
    summary: str = Field(description="Short synopsis of endpoint functionality")
    request_body_schema: Optional[str] = Field(
        default=None,
        description="JSON schema or Pydantic representation of the request payload"
    )
    response_schema_200: Optional[str] = Field(
        default=None,
        description="JSON schema or description of successful HTTP 200/201 response"
    )
    response_schema_error: Optional[str] = Field(
        default=None,
        description="Standard error structure (e.g., RFC 7807 Problem Details)"
    )
    auth_required: bool = Field(default=True, description="Authentication / authorization requirement")


class ArchitectureSpec(BaseModel):
    """Deterministic output contract for architecture_design_task."""
    system_overview: str = Field(description="High-level architectural vision and system context")
    architectural_pattern: str = Field(
        description="Core design pattern (e.g., Clean Architecture, Modular Monolith, Hexagonal)"
    )
    component_boundaries: List[str] = Field(
        description="Logical subsystems and decoupling boundaries"
    )
    technology_stack: Dict[str, str] = Field(
        description="Key runtime technologies: runtime, framework, database, cache, orm"
    )
    data_models: List[DatabaseSchemaModel] = Field(
        description="Detailed database schema blueprints"
    )
    api_endpoints: List[ApiEndpoint] = Field(
        description="Standardized API route definitions"
    )
    non_functional_requirements: Dict[str, List[str]] = Field(
        description="Categorized NFRs (Security, Scalability, Observability, Performance)"
    )
    directory_structure: str = Field(
        description="Canonical directory and file layout representation"
    )


# ==============================================================================
# Phase 3: Senior Developer Implementation Schemas
# ==============================================================================

class GeneratedFile(BaseModel):
    """Individual source code or configuration file generated by the engineer."""
    file_path: str = Field(
        description="Relative project path (e.g., 'src/api/routes.py', 'src/models/user.py')"
    )
    description: str = Field(description="Summary of module purpose and key classes/functions")
    content: str = Field(description="Full, production-ready, unabridged source code")


class SprintImplementation(BaseModel):
    """Deterministic output contract for sprint_implementation_task."""
    codebase_summary: str = Field(
        description="Executive summary of implemented features and architectural compliance"
    )
    primary_language: str = Field(description="Programming language used (e.g., Python 3.12)")
    framework: str = Field(description="Web/application framework used (e.g., FastAPI)")
    files: List[GeneratedFile] = Field(
        description="Complete list of all generated application source files"
    )
    setup_instructions: str = Field(
        description="CLI commands and environment variables required to run locally"
    )


# ==============================================================================
# Phase 4: QA & Security Automation Schemas
# ==============================================================================

class TestCaseResult(BaseModel):
    """Individual automated test execution record."""
    test_id: str = Field(description="Identifier corresponding to Acceptance Criterion, e.g., 'TEST-AC-001'")
    target_story_id: str = Field(description="Associated User Story ID, e.g., 'US-101'")
    test_name: str = Field(description="Descriptive test function or scenario name")
    test_type: Literal["unit", "integration", "security", "property"] = Field(
        description="Classification of test level"
    )
    test_code: str = Field(description="Executable pytest test implementation code")
    expected_outcome: str = Field(description="Verification condition assert statement expectation")
    status: Literal["PASSED", "FAILED", "SKIPPED"] = Field(
        description="Result of test verification"
    )


class DefectItem(BaseModel):
    """Structured defect or vulnerability identified during QA."""
    defect_id: str = Field(description="Defect tracking ID, e.g., 'DEF-001'")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(
        description="Impact severity rating"
    )
    title: str = Field(description="Concise description of the failure or vulnerability")
    description: str = Field(description="Detailed observed behavior vs. expected specification")
    steps_to_reproduce: str = Field(description="Reproduction procedure")
    remediation_steps: str = Field(description="Concrete recommendation to rectify the issue")


class QAReport(BaseModel):
    """Deterministic output contract for qa_verification_task."""
    total_tests: int = Field(description="Total number of automated tests executed")
    passed_tests: int = Field(description="Number of passing tests")
    failed_tests: int = Field(description="Number of failing tests")
    code_coverage_percentage: float = Field(
        description="Estimated branch or line test coverage percentage"
    )
    test_cases: List[TestCaseResult] = Field(
        description="Exhaustive test suite covering all Gherkin acceptance criteria"
    )
    defects: List[DefectItem] = Field(
        default_factory=list,
        description="Catalog of discovered bugs, unhandled edge cases, or security issues"
    )
    owasp_security_audit: Dict[str, str] = Field(
        description="OWASP Top 10 assessment breakdown (e.g., Injection, Broken Auth, SSRF)"
    )
    sign_off_status: Literal["APPROVED", "APPROVED_WITH_CONDITIONS", "REJECTED"] = Field(
        description="Formal QA release recommendation"
    )
    qa_notes: str = Field(description="Summary narrative and risk mitigation commentary")


# ==============================================================================
# Phase 5: DevOps & Release Package Schemas
# ==============================================================================

class DevOpsArtifacts(BaseModel):
    """Infrastructure-as-code and deployment assets."""
    dockerfile_content: str = Field(
        description="Production multi-stage Dockerfile adhering to container security best practices"
    )
    docker_compose_content: str = Field(
        description="Multi-service docker-compose.yml including database, cache, and app services"
    )
    github_actions_ci_cd: str = Field(
        description="Complete GitHub Actions workflow YAML (.github/workflows/pipeline.yml)"
    )
    env_template: str = Field(
        description="Production .env.example with documented configuration parameters"
    )


class SprintReleasePackage(BaseModel):
    """Deterministic output contract for deployment_and_sprint_review_task."""
    sprint_goal: str = Field(description="Sprint goal evaluated for fulfillment")
    release_version: str = Field(description="Semantic version tag, e.g., 'v1.0.0'")
    deployment_artifacts: DevOpsArtifacts = Field(
        description="Ready-to-deploy containerization and CI/CD assets"
    )
    release_readiness_score: float = Field(
        description="Composite score (0.0 to 100.0) reflecting code quality, QA signoff, and DevOps readiness"
    )
    sprint_review_summary: str = Field(
        description="Executive summary of sprint outcomes, shipped user stories, and business value"
    )
    retrospective_observations: List[str] = Field(
        description="Agile retrospective insights: what went well, bottlenecks, and process kaizen"
    )
    release_signoff: bool = Field(
        description="Binary decision whether the package is cleared for production deployment"
    )
