"""Pydantic models and validation schemas for ofrendas."""

from datetime import datetime, timezone
from typing import List, Literal, Optional
import uuid

from pydantic import BaseModel, Field, field_validator


class OfrendaCreate(BaseModel):
    """Payload to create a new ofrenda."""

    name: str = Field(..., min_length=1, max_length=80)
    relationship: Optional[str] = Field(None, max_length=40)
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    language: Literal["en", "es"] = "es"
    foods: List[str] = Field(default_factory=list, max_length=12)
    drinks: List[str] = Field(default_factory=list, max_length=6)
    songs: List[str] = Field(default_factory=list, max_length=6)
    objects: List[str] = Field(default_factory=list, max_length=8)
    story_text: Optional[str] = Field(None, max_length=5000)

    @field_validator("name")
    def name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Name cannot be empty or whitespace only")
        return trimmed

    @field_validator("foods", "drinks", "songs", "objects")
    def validate_item_lengths(cls, items: List[str]) -> List[str]:
        for item in items:
            if len(item) > 60:
                raise ValueError("Item exceeds maximum length of 60 characters")
        return items


class OfrendaUpdate(BaseModel):
    """Payload to update an existing ofrenda."""

    name: Optional[str] = Field(None, min_length=1, max_length=80)
    relationship: Optional[str] = Field(None, max_length=40)
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    language: Optional[Literal["en", "es"]] = None
    foods: Optional[List[str]] = Field(None, max_length=12)
    drinks: Optional[List[str]] = Field(None, max_length=6)
    songs: Optional[List[str]] = Field(None, max_length=6)
    objects: Optional[List[str]] = Field(None, max_length=8)
    story_text: Optional[str] = Field(None, max_length=5000)
    transcript: Optional[str] = None
    remembrance: Optional[str] = None
    generated_by: Optional[str] = None
    model_used: Optional[str] = None

    @field_validator("name")
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Name cannot be empty or whitespace only")
            return trimmed
        return None

    @field_validator("foods", "drinks", "songs", "objects")
    def validate_item_lengths(cls, items: Optional[List[str]]) -> Optional[List[str]]:
        if items is not None:
            for item in items:
                if len(item) > 60:
                    raise ValueError("Item exceeds maximum length of 60 characters")
        return items


class OfrendaRecord(BaseModel):
    """Complete persisted ofrenda record."""

    id: str
    created_at: str
    name: str = Field(..., min_length=1, max_length=80)
    relationship: Optional[str] = Field(None, max_length=40)
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    language: Literal["en", "es"] = "es"
    foods: List[str] = Field(default_factory=list, max_length=12)
    drinks: List[str] = Field(default_factory=list, max_length=6)
    songs: List[str] = Field(default_factory=list, max_length=6)
    objects: List[str] = Field(default_factory=list, max_length=8)
    story_text: Optional[str] = Field(None, max_length=5000)
    transcript: Optional[str] = None
    photo: Optional[str] = None
    remembrance: Optional[str] = None
    generated_by: Optional[str] = None
    model_used: Optional[str] = None


class OfrendaSummary(BaseModel):
    """Summary of an ofrenda for listings."""

    id: str
    name: str
    created_at: str
    relationship: Optional[str] = None
    photo: Optional[str] = None


class GenerateRequest(BaseModel):
    """Optional payload for remembrance generation."""

    model: Optional[str] = None
