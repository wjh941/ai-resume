from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BasicInfo(BaseModel):
    name: str
    phone: str
    email: str
    city: str


class JobPreference(BaseModel):
    target_role: str
    employment_type: str = ""
    expected_salary: str = ""


class EducationItem(BaseModel):
    school: str
    major: str = ""
    degree: str = ""
    start_date: str = ""
    end_date: str = ""


class EmploymentItem(BaseModel):
    company: str
    position: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class ProjectItem(BaseModel):
    name: str
    role: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class SkillCertificateInfo(BaseModel):
    skills: list[str] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)


class SectionVisibility(BaseModel):
    basic: bool = True
    job: bool = True
    education: bool = True
    employment: bool = True
    projects: bool = True
    skills: bool = True
    self_evaluation: bool = True


class ResumePayload(BaseModel):
    version: Literal[1] = 1
    basic: BasicInfo
    job: JobPreference
    education: list[EducationItem] = Field(default_factory=list)
    employment: list[EmploymentItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    skills: SkillCertificateInfo
    self_evaluation: str = ""
    section_visibility: SectionVisibility = Field(default_factory=SectionVisibility)
