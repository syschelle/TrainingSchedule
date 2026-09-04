from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BlockType(str, Enum):
    training = "training"
    break_block = "break"
    lunch = "lunch"
    arrival = "arrival"
    departure = "departure"


class PlanningSettings(BaseModel):
    day_start: str = "08:30"
    day_end: str = "17:00"
    break_min_minutes: int = 20
    break_max_minutes: int = 30
    break_preferred_minutes: int = 25
    lunch_minutes: int = 45
    lunch_window_start: str = "12:00"
    lunch_window_end: str = "14:00"
    monday_arrival_enabled: bool = True
    monday_arrival_start: str = "08:30"
    monday_arrival_end: str = "10:00"
    monday_arrival_label: str = "Anreise / Eintreffen der Teilnehmer"
    thursday_departure_enabled: bool = True
    thursday_departure_start: str = "15:00"
    thursday_departure_end: str = "17:00"
    thursday_departure_label: str = "Abreise"


class TrainingTopic(BaseModel):
    id: str
    product_id: str = "deepunity-pacs"
    participant_group_id: str | None = None
    participant_group_ids: list[str] = Field(default_factory=list)
    title: str
    description: str = ""
    duration_minutes: int = Field(gt=0)
    catalog_duration_minutes: int | None = Field(default=None, gt=0)
    duration_overridden: bool = False
    priority: int = 3
    preferred_day: str | None = None
    preferred_order: int | None = None
    depends_on: str | None = None
    trainer: str = ""
    room: str = ""
    notes: str = ""
    participants_per_session: int | None = None
    sessions_required: float | None = None
    split_enabled: bool = False
    split_part: int | None = None
    split_parts: int | None = None
    split_sequence_id: str | None = None
    background_color: str = "#eaf8f2"


class ScheduleBlock(BaseModel):
    id: str
    type: BlockType
    week: int = 1
    day: str
    title: str
    start: str
    end: str
    topic_id: str | None = None
    source_topic_id: str | None = None
    split_part: int | None = None
    split_parts: int | None = None
    description: str = ""
    trainer: str = ""
    room: str = ""
    notes: str = ""
    background_color: str = "#ffffff"


class ParticipantGroup(BaseModel):
    id: str
    product_id: str = "deepunity-pacs"
    name: str
    participant_count: int = 0
    notes: str = ""


class ProductLine(BaseModel):
    id: str
    name: str
    description: str = ""
    participant_groups: list[ParticipantGroup] = Field(default_factory=list)


class TrainerWeekAvailability(BaseModel):
    trainer: str
    week: int = Field(ge=1)
    weekdays: list[Literal["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]] = Field(default_factory=list)


class TrainingProject(BaseModel):
    title: str = "DeepUnity Schulungsplan"
    project_mode: Literal["training_plan", "service_calculation"] = "training_plan"
    customer_data_required: bool = True
    customer_name: str = ""
    location: str = ""
    product_id: str = "deepunity-pacs"
    trainer: str = ""
    trainers: list[str] = Field(default_factory=list)
    participant_group: str = ""
    product_lines: list[ProductLine] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    settings: PlanningSettings = Field(default_factory=PlanningSettings)
    topics: list[TrainingTopic] = Field(default_factory=list)
    blocks: list[ScheduleBlock] = Field(default_factory=list)
    manual_weeks: list[int] = Field(default_factory=list)
    trainer_availability: list[TrainerWeekAvailability] = Field(default_factory=list)
    unscheduled_topics: list[TrainingTopic] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_trainers(self) -> "TrainingProject":
        cleaned: list[str] = []
        for value in self.trainers:
            name = str(value).strip()
            if name and name not in cleaned:
                cleaned.append(name)
        legacy = self.trainer.strip()
        if not cleaned and legacy:
            cleaned.append(legacy)
        self.trainers = cleaned
        self.trainer = cleaned[0] if cleaned else ""
        if cleaned:
            for block in self.blocks:
                if not block.trainer.strip():
                    block.trainer = cleaned[0]
        return self


class ImportSummary(BaseModel):
    excel: dict
    pdfs: list[dict]
    project: TrainingProject


class TrainingContentUpdate(BaseModel):
    title: str
    target_group: str = ""
    duration_minutes: int = Field(gt=0)
    max_participants: int | None = Field(default=None, gt=0)
    split_enabled: bool = False
    dependency_content_id: str | None = None
    participant_group_ids: list[str] = Field(default_factory=list)
    background_color: str = "#eaf8f2"
    goals: str = ""
    requirements: str = ""
    preparation: str = ""
    special_notes: str = ""


class TrainingContentMarkdownUpdate(BaseModel):
    markdown_content: str = ""
    change_type: Literal["saved", "docx_imported"] = "saved"


class TrainingContentCreate(BaseModel):
    product_id: str
    title: str


class ProductCreate(BaseModel):
    name: str
    description: str = ""


class ProjectFile(BaseModel):
    format: Literal["schulungsplantool-project"] = "schulungsplantool-project"
    schema_version: int = 1
    app_version: str = ""
    exported_at: str = ""
    project: TrainingProject


class CustomerPlanningMove(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_id: str
    week: int = Field(ge=1)
    day: Literal["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
    trainer: str
    start: str
    end: str


class CustomerPlanningExchange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: Literal["schulungsplantool-customer-package"] = "schulungsplantool-customer-package"
    schema_version: Literal[1] = 1
    exchange_id: str
    exported_at: str
    baseline: TrainingProject
    signature: str


class CustomerPlanningReturn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: Literal["schulungsplantool-customer-return"] = "schulungsplantool-customer-return"
    schema_version: Literal[1] = 1
    returned_at: str = ""
    exchange: CustomerPlanningExchange
    moves: list[CustomerPlanningMove] = Field(default_factory=list)


class ExportRequest(BaseModel):
    project: TrainingProject
    format: Literal["pdf"]
