from typing import List, Optional

from pydantic import BaseModel, Field


class RelatedFigure(BaseModel):
    label: str = Field(
        ..., description="The figure reference label, such as 'Fig. 1' or 'Figure 3'."
    )
    description: str = Field(
        ...,
        description="Brief description of what the figure shows or how it relates to the table.",
    )


class TableMetadataResponse(BaseModel):
    title: str = Field(
        ...,
        description="A short, descriptive title for the table (max 15 words) summarizing its purpose.",
    )
    summary: str = Field(
        ...,
        description="A concise 1–2 sentence explanation of what the table shows, including design or safety context if relevant.",
    )
    keywords: List[str] = Field(
        ...,
        description="5–10 relevant keywords or phrases describing the subject of the table for semantic search.",
    )
    dates: Optional[List[str]] = Field(
        default=None,
        description="Dates mentioned in or around the table (e.g. 'March 2022', 'Q3 2021').",
    )
    locations: Optional[List[str]] = Field(
        default=None,
        description="Geographic or organizational locations referenced near the table (e.g. 'Europe', 'Head Office').",
    )
    entities: Optional[List[str]] = Field(
        default=None,
        description="Named entities such as product names, standards, models, or companies mentioned near the table.",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="The name or identifier of the model or product referenced by the table (e.g., 'BBV43').",
    )
    component_type: Optional[str] = Field(
        default=None,
        description="The engineering or industrial component this table describes (e.g., 'Boiler Blowdown Valve').",
    )
    application_context: Optional[List[str]] = Field(
        default=None,
        description="Broader application or industry contexts where this table applies (e.g., 'steam systems', 'boiler safety').",
    )

    related_figures: Optional[List[RelatedFigure]] = Field(
        default=None,
        description="List of figure labels or references (e.g., 'Fig. 1') mentioned near the table that help interpret it visually.",
    )


class MatchedSection(BaseModel):
    section_number: int
    section_title: str
    matched_chapters: List[str]


class QuestionMappingResponse(BaseModel):
    question: str
    matched_sections: List[MatchedSection]


class SubQuestionMapping(BaseModel):
    sub_question: str
    section_number: int
    section_title: str
    matched_chapters: List[str]


class QueryDecompositionResponse(BaseModel):
    original_question: str
    decomposed_questions: List[SubQuestionMapping]
