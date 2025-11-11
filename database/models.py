"""SQLAlchemy ORM models for CyberIntel Summarizer."""

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class CVE(Base):
    """Model for storing CVE (Common Vulnerabilities and Exposures) data."""

    __tablename__ = "cves"

    # Primary key
    cve_id = Column(String(20), primary_key=True, index=True)  # e.g., CVE-2025-1234

    # Core CVE information
    description = Column(Text, nullable=False)
    published_date = Column(DateTime, nullable=False, index=True)
    last_modified = Column(DateTime, nullable=False, index=True)  # Index for update detection

    # Severity and scoring
    severity = Column(String(20), index=True)  # Critical, High, Medium, Low, None
    cvss_score = Column(Float, nullable=True)  # 0.0 - 10.0
    cvss_vector = Column(String(100), nullable=True)  # CVSS vector string
    attack_vector = Column(String(20), nullable=True)  # Network, Adjacent, Local, Physical
    attack_complexity = Column(String(20), nullable=True)  # Low, High
    privileges_required = Column(String(20), nullable=True)  # None, Low, High
    user_interaction = Column(String(20), nullable=True)  # None, Required

    # Affected products
    vendor = Column(String(100), nullable=True, index=True)
    product = Column(String(100), nullable=True)
    version = Column(String(50), nullable=True)

    # Additional metadata
    source = Column(String(20), nullable=False, index=True, default="NVD")  # NVD, CISA, etc.
    references = Column(JSON, nullable=True)  # List of reference URLs
    cwe_ids = Column(JSON, nullable=True)  # Common Weakness Enumeration IDs

    # LLM-generated fields (Phase 2)
    summary = Column(Text, nullable=True)
    summary_generated_at = Column(DateTime, nullable=True)

    # Raw data storage
    raw_data = Column(JSON, nullable=True)  # Full JSON response from source

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<CVE(cve_id='{self.cve_id}', severity='{self.severity}', published='{self.published_date}')>"

    def to_dict(self) -> dict:
        """Convert CVE object to dictionary."""
        return {
            "cve_id": self.cve_id,
            "description": self.description,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "cvss_vector": self.cvss_vector,
            "attack_vector": self.attack_vector,
            "attack_complexity": self.attack_complexity,
            "privileges_required": self.privileges_required,
            "user_interaction": self.user_interaction,
            "vendor": self.vendor,
            "product": self.product,
            "version": self.version,
            "source": self.source,
            "references": self.references,
            "cwe_ids": self.cwe_ids,
            "summary": self.summary,
            "summary_generated_at": (
                self.summary_generated_at.isoformat() if self.summary_generated_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Association table for many-to-many relationship between scans and CVEs
scan_cves = Table(
    "scan_cves",
    Base.metadata,
    Column("scan_id", Integer, ForeignKey("scans.id"), primary_key=True),
    Column("cve_id", String(20), ForeignKey("cves.cve_id"), primary_key=True),
    Column("dependency_id", Integer, ForeignKey("dependencies.id"), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)


class Scan(Base):
    """Model for storing dependency scan results."""

    __tablename__ = "scans"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User ownership (for multi-tenant support)
    user_id = Column(String(36), nullable=True, index=True)  # UUID from Supabase auth

    # Scan metadata
    file_name = Column(String(255), nullable=False)  # e.g., package.json
    file_type = Column(String(50), nullable=False)  # npm, pip, go, ruby, maven
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash of file content
    scan_date = Column(DateTime, nullable=False, server_default=func.now())

    # Scan results summary
    total_dependencies = Column(Integer, default=0)
    vulnerable_dependencies = Column(Integer, default=0)
    total_cves = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)

    # Raw file content (optional, for debugging)
    raw_content = Column(Text, nullable=True)

    # Relationships
    dependencies = relationship("Dependency", back_populates="scan", cascade="all, delete-orphan")
    cves = relationship("CVE", secondary=scan_cves, backref="scans")

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Scan(id={self.id}, file='{self.file_name}', type='{self.file_type}', vulnerable={self.vulnerable_dependencies}/{self.total_dependencies})>"

    def to_dict(self) -> dict:
        """Convert Scan object to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_hash": self.file_hash,
            "scan_date": self.scan_date.isoformat() if self.scan_date else None,
            "total_dependencies": self.total_dependencies,
            "vulnerable_dependencies": self.vulnerable_dependencies,
            "total_cves": self.total_cves,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Dependency(Base):
    """Model for storing parsed dependency information."""

    __tablename__ = "dependencies"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to scan
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)

    # Dependency information
    package_name = Column(String(255), nullable=False, index=True)
    version = Column(String(100), nullable=False)
    version_constraint = Column(String(100), nullable=True)  # e.g., ">=4.0.0", "^1.2.3"
    ecosystem = Column(String(50), nullable=False)  # npm, pip, go, ruby, maven

    # CPE matching information
    cpe_uri = Column(String(255), nullable=True)  # Matched CPE URI from NVD
    cpe_match_confidence = Column(Float, nullable=True)  # 0.0-1.0 confidence score

    # Vulnerability status
    is_vulnerable = Column(Integer, default=0)  # 0 = safe, 1 = vulnerable
    cve_count = Column(Integer, default=0)
    highest_severity = Column(String(20), nullable=True)  # Critical, High, Medium, Low

    # Additional metadata
    package_metadata = Column(
        JSON, nullable=True
    )  # Additional package info (description, license, etc.)

    # Relationships
    scan = relationship("Scan", back_populates="dependencies")
    cves = relationship("CVE", secondary=scan_cves, backref="dependencies")

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Dependency(id={self.id}, package='{self.package_name}', version='{self.version}', vulnerable={self.is_vulnerable})>"

    def to_dict(self) -> dict:
        """Convert Dependency object to dictionary."""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "package_name": self.package_name,
            "version": self.version,
            "version_constraint": self.version_constraint,
            "ecosystem": self.ecosystem,
            "cpe_uri": self.cpe_uri,
            "cpe_match_confidence": self.cpe_match_confidence,
            "is_vulnerable": self.is_vulnerable,
            "cve_count": self.cve_count,
            "highest_severity": self.highest_severity,
            "package_metadata": self.package_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChatSession(Base):
    """Model for storing chat sessions (Phase 5)."""

    __tablename__ = "chat_sessions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User ownership (for multi-tenant support)
    user_id = Column(String(36), nullable=True, index=True)  # UUID from Supabase auth

    # Foreign key to scan (optional - can have general chats)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True, index=True)

    # Session metadata
    title = Column(String(255), nullable=True)  # Optional session title
    session_type = Column(String(20), nullable=False, default="project")  # project or general

    # Dependency context (Phase 5 enhancement)
    selected_dependency_ids = Column(JSON, nullable=True)  # List of dependency IDs for focused chat
    context_injected = Column(
        Integer, nullable=False, default=0
    )  # Boolean: has full context been injected (0=no, 1=yes)

    # Smart context tracking (Phase 6 enhancement - conditional injection)
    dependency_context_hash = Column(
        String(64), nullable=True
    )  # SHA256 hash of selected_dependency_ids for change detection
    last_context_used_at = Column(
        DateTime, nullable=True
    )  # When dependency context was last injected
    context_usage_count = Column(
        Integer, nullable=False, default=0
    )  # How many times context has been injected

    # Unified chat architecture (Phase 6 - unified chat)
    context_stack = Column(
        Text, nullable=True
    )  # JSON: Stack of ChatContext objects for rollback support
    enabled_features = Column(
        Text, nullable=True
    )  # JSON: Set of enabled feature flags for this session

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_message_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    scan = relationship("Scan", backref="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, type='{self.session_type}', scan_id={self.scan_id})>"

    def to_dict(self) -> dict:
        """Convert ChatSession object to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scan_id": self.scan_id,
            "title": self.title,
            "session_type": self.session_type,
            "selected_dependency_ids": self.selected_dependency_ids,
            "context_injected": bool(self.context_injected),
            "dependency_context_hash": self.dependency_context_hash,
            "last_context_used_at": (
                self.last_context_used_at.isoformat() if self.last_context_used_at else None
            ),
            "context_usage_count": self.context_usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "message_count": len(self.messages) if self.messages else 0,
        }


class ChatMessage(Base):
    """Model for storing individual chat messages (Phase 5)."""

    __tablename__ = "chat_messages"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to session
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Context used for this message (for debugging/audit)
    context_cves = Column(JSON, nullable=True)  # List of CVE IDs used in context
    rag_query = Column(Text, nullable=True)  # Original query sent to RAG

    # Smart context tracking (Phase 6 enhancement - conditional injection)
    context_injected = Column(
        Integer, nullable=False, default=0
    )  # Boolean: was dependency context injected for this message (0=no, 1=yes)
    context_dependency_count = Column(
        Integer, nullable=True
    )  # How many dependencies were in context

    # Token usage tracking
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)

    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<ChatMessage(id={self.id}, role='{self.role}', content='{preview}')>"

    def to_dict(self) -> dict:
        """Convert ChatMessage object to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "context_cves": self.context_cves,
            "context_injected": bool(self.context_injected),
            "context_dependency_count": self.context_dependency_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
