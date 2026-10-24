"""Pydantic Data Contracts for Agile Dev Crew (Pod Architecture).

Strict schema definitions enforcing deterministic handoffs across pods:
- Pod A (Product & Design):
    1. Product Owner  -> SprintBacklog
    2. UI/UX Designer -> DesignSystemSpec
- Pod B (Engineering & Implementation):
    3. System Architect  -> ArchitectureSpec
    4. Backend Developer -> BackendImplementation
    5. Frontend Developer -> FrontendImplementation
    6. Engineering Pod    -> FullStackImplementation
- Pod C (Verification & Delivery):
    7. QA Engineer       -> QAReport
    8. DevOps / Scrum    -> SprintReleasePackage
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Phase 1: Product Owner & Backlog Schemas (Pod A)
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
# Phase 2: UI/UX Design System Schemas (Pod A)
# ==============================================================================

class UIComponentSpec(BaseModel):
    """Atomic UI component blueprint designed by UI/UX designer."""
    component_name: str = Field(description="Component identifier, e.g., 'WebhookDeliveryCard'")
    description: str = Field(description="Visual intent and interaction patterns")
    props: Dict[str, str] = Field(
        description="Expected UI properties and data types (e.g., {'status': 'string', 'retryCount': 'number'})"
    )
    visual_states: List[str] = Field(
        description="Visual state variants: default, hover, active, loading, disabled, error"
    )
    tailwind_classes: str = Field(
        description="Tailwind CSS v4 utility classes defining the styling"
    )
    accessibility_attributes: List[str] = Field(
        description="WCAG 2.1 AA attributes (e.g., 'aria-live=\"polite\"', 'role=\"status\"')"
    )


class WireframeLayout(BaseModel):
    """Page layout structure and responsive wireframe specification."""
    page_name: str = Field(description="Page identifier, e.g., 'DashboardView', 'SubscriptionDetail'")
    route_path: str = Field(description="Client URL route path, e.g., '/', '/subscriptions/:id'")
    layout_structure: str = Field(
        description="Wireframe hierarchy description (e.g., Sidebar + TopNav + Responsive 3-col Grid)"
    )
    responsive_breakpoints: Dict[str, str] = Field(
        description="Layout adjustments for mobile (sm), tablet (md), and desktop (lg/xl)"
    )
    user_interactions: List[str] = Field(
        description="Step-by-step micro-interactions and transitions"
    )


class DesignSystemSpec(BaseModel):
    """Deterministic output contract for ui_ux_design_task."""
    theme_name: str = Field(description="Design system theme identifier")
    color_palette: Dict[str, str] = Field(
        description="Semantic color palette (primary, secondary, background, surface, text, accents, error)"
    )
    typography: Dict[str, str] = Field(
        description="Font families, font sizes, line heights, and weights"
    )
    spacing_and_radii: Dict[str, str] = Field(
        description="Standard spacing units, border radii, and drop shadows"
    )
    components: List[UIComponentSpec] = Field(
        description="Atomic UI components specification"
    )
    layouts: List[WireframeLayout] = Field(
        description="Comprehensive wireframes for all user-facing views"
    )
    wcag_compliance_checklist: List[str] = Field(
        description="Accessibility guarantees (contrast ratio >= 4.5:1, keyboard focusable, screen reader friendly)"
    )


class ProductDesignPackage(BaseModel):
    """Aggregated output from Pod A (Product & Design Pod)."""
    sprint_backlog: SprintBacklog
    design_system: DesignSystemSpec


# ==============================================================================
# Phase 3: Architecture & Engineering Schemas (Pod B)
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
    """Deterministic output contract for architecture_contract_task."""
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


class GeneratedFile(BaseModel):
    """Individual source code or configuration file generated by an engineer."""
    file_path: str = Field(
        description="Relative project path (e.g., 'backend/api/routes.py', 'frontend/components/Card.tsx')"
    )
    description: str = Field(description="Summary of module purpose and key classes/functions")
    content: str = Field(description="Full, production-ready, unabridged source code")


class BackendImplementation(BaseModel):
    """Deterministic output contract for backend_development_task."""
    codebase_summary: str = Field(description="Overview of backend models, services, and APIs implemented")
    primary_language: str = Field(default="Python 3.12")
    framework: str = Field(default="FastAPI")
    orm_and_db_models: List[GeneratedFile] = Field(description="Database models and migrations")
    api_endpoints_and_routers: List[GeneratedFile] = Field(description="REST API controllers and routes")
    service_layer_and_business_logic: List[GeneratedFile] = Field(description="Core domain services")
    configuration_and_utilities: List[GeneratedFile] = Field(description="Config, auth, and helper modules")
    setup_and_run_instructions: str = Field(description="CLI steps to run the backend service")


class FrontendImplementation(BaseModel):
    """Deterministic output contract for frontend_development_task."""
    codebase_summary: str = Field(description="Overview of client components, views, and routing")
    framework: str = Field(default="Next.js 14 (App Router) + TypeScript")
    styling: str = Field(default="Tailwind CSS v4")
    ui_components: List[GeneratedFile] = Field(description="Reusable Atomic UI components")
    pages_and_views: List[GeneratedFile] = Field(description="Page routes and layout templates")
    api_client_and_state: List[GeneratedFile] = Field(description="API fetchers, hooks, and client state")
    styling_and_theme_files: List[GeneratedFile] = Field(description="Tailwind config and CSS definitions")
    setup_and_run_instructions: str = Field(description="CLI steps to run the frontend application")


class FullStackImplementation(BaseModel):
    """Aggregated output from Pod B (Engineering Pod)."""
    architecture_spec: ArchitectureSpec
    backend: BackendImplementation
    frontend: FrontendImplementation
    integration_notes: str = Field(description="Cross-tier integration and environment wiring notes")


# Backward compatibility alias
class SprintImplementation(BaseModel):
    """Generic implementation wrapper for backwards compatibility."""
    codebase_summary: str
    primary_language: str
    framework: str
    files: List[GeneratedFile]
    setup_instructions: str


# ==============================================================================
# Phase 4: QA & Security Automation Schemas (Pod C)
# ==============================================================================

class TestCaseResult(BaseModel):
    """Individual automated test execution record."""
    test_id: str = Field(description="Identifier corresponding to Acceptance Criterion, e.g., 'TEST-AC-001'")
    target_story_id: str = Field(description="Associated User Story ID, e.g., 'US-101'")
    test_name: str = Field(description="Descriptive test function or scenario name")
    test_type: Literal["unit", "integration", "security", "property", "ui_component"] = Field(
        description="Classification of test level"
    )
    target_tier: Literal["backend", "frontend", "fullstack"] = Field(
        default="backend",
        description="Target tier under test"
    )
    test_code: str = Field(description="Executable test implementation code")
    expected_outcome: str = Field(description="Verification condition assert statement expectation")
    status: Literal["PASSED", "FAILED", "SKIPPED"] = Field(
        description="Result of test verification"
    )


class DefectItem(BaseModel):
    """Structured defect or vulnerability identified during QA."""
    defect_id: str = Field(description="Defect tracking ID, e.g., 'DEF-001'")
    target_tier: Literal["backend", "frontend", "architecture", "ui_ux"] = Field(
        description="Tier responsible for remediating this defect"
    )
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
    accessibility_audit: Dict[str, str] = Field(
        default_factory=dict,
        description="WCAG 2.1 AA a11y audit results for frontend components"
    )
    sign_off_status: Literal["APPROVED", "APPROVED_WITH_CONDITIONS", "REJECTED"] = Field(
        description="Formal QA release recommendation"
    )
    qa_notes: str = Field(description="Summary narrative and risk mitigation commentary")


# ==============================================================================
# Phase 5: DevOps & Release Package Schemas (Pod C)
# ==============================================================================

class DevOpsArtifacts(BaseModel):
    """Infrastructure-as-code and deployment assets."""
    dockerfile_backend: str = Field(description="Multi-stage Dockerfile for the backend service")
    dockerfile_frontend: str = Field(description="Multi-stage Dockerfile for the frontend client")
    docker_compose_content: str = Field(
        description="Full-stack docker-compose.yml orchestrating database, cache, backend, and frontend"
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
