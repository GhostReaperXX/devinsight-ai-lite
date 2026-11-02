"""Table models: each class is one table, each attribute one column."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin', 'member')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # Only a salted hash is stored. The password itself can never be read back.
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="member")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    issues: Mapped[list["Issue"]] = relationship(back_populates="project")


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        CheckConstraint(
            "category IN ('bug', 'feature', 'documentation', 'performance', 'security')",
            name="ck_issues_category",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="ck_issues_priority",
        ),
        CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved', 'closed')",
            name="ck_issues_status",
        ),
        CheckConstraint(
            "prediction_confidence IS NULL OR prediction_confidence BETWEEN 0 AND 1",
            name="ck_issues_confidence",
        ),
        Index("ix_issues_project_status", "project_id", "status"),
        Index("ix_issues_category", "category"),
        Index("ix_issues_assignee", "assignee_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"))
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    duplicate_of_id: Mapped[int | None] = mapped_column(
        ForeignKey("issues.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(20))
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    status: Mapped[str] = mapped_column(String(15), default="open")
    # What the model suggested, kept beside what the person chose, to measure agreement.
    predicted_category: Mapped[str | None] = mapped_column(String(20))
    prediction_confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(back_populates="issues")
    reporter: Mapped["User"] = relationship(foreign_keys=[reporter_id])
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])
    duplicate_of: Mapped["Issue | None"] = relationship(remote_side=[id])
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan", order_by="Comment.id"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    issue: Mapped["Issue"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship()
