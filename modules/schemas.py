"""Typed contracts for values shared by the profile, matcher, and interview UI."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class _Record(BaseModel):
    model_config = ConfigDict(extra="allow")


class UserProfile(_Record):
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    experience: str = ""
    levels: dict[str, StrictInt] = Field(default_factory=dict)

    @field_validator("levels")
    @classmethod
    def levels_are_bounded(cls, levels: dict[str, int]) -> dict[str, int]:
        if any(level < 0 or level > 3 for level in levels.values()):
            raise ValueError("Level phải nằm trong khoảng 0–3.")
        return levels


class RoleSkill(_Record):
    name: str = Field(min_length=1)
    level: StrictInt | None = Field(default=None, ge=0, le=3)
    weight: float = Field(default=1, gt=0)


class RoleRequirement(_Record):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    skills: list[RoleSkill | str] = Field(default_factory=list)


class GapItem(_Record):
    skill: str = Field(min_length=1)
    required: StrictInt = Field(ge=0, le=3)
    current: StrictInt = Field(ge=0, le=3)
    gap: StrictInt = Field(ge=0, le=3)
    priority: float = Field(ge=0)
    status: str


class GapAnalysisResult(_Record):
    role_id: str | None = None
    items: list[GapItem] = Field(default_factory=list)
    match_percent: float = Field(ge=0, le=100)
    missing: list[str] = Field(default_factory=list)


class InterviewFeedback(_Record):
    reference_answer: str = Field(min_length=1)
    has_reference_answer: bool
    good_answer_points: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    time_minutes: float | None = None
    question_type: str
    content_reviewed: bool
    quality: str
    quality_label: str


class CriterionVerdict(_Record):
    point: str
    met: bool
    evidence: str = ""


class AnswerReview(_Record):
    score: float = Field(ge=0, le=10)
    criteria: list[CriterionVerdict]
    red_flags_hit: list[str] = Field(default_factory=list)
    feedback: str
    improvement: str = ""
    source: Literal["llm", "offline_rubric"]
    model: str | None = None
    fallback_reason: str | None = None
