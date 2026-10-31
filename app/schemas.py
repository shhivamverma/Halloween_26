"""Pydantic models and validation schemas for ofrendas and optional voice recreation."""

from datetime import datetime, timezone
from typing import List, Literal, Optional
import uuid

from pydantic import BaseModel, Field, field_validator, model_validator


class VoiceConsentRecord(BaseModel):
    """Certified family permission record required for voice recreation."""

    authorized_by: str = Field(..., min_length=1, max_length=100)
    confirmed_permission: bool = Field(..., description="Explicit affirmative family consent")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    statement: str = Field(
        default="I certify that I have explicit family authorization to generate an AI voice recreation for memorial purposes."
    )

    @field_validator("confirmed_permission")
    def must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Affirmative family authorization is strictly required for voice recreation.")
        return v


class VoiceProfileMetadata(BaseModel):
    """Metadata regarding local voice recreation state and provenance."""

    has_reference: bool = False
    reference_filename: Optional[str] = None
    reference_duration_s: Optional[float] = None
    has_synthesized_audio: bool = False
    synthesized_filename: Optional[str] = None
    synthesized_duration_s: Optional[float] = None
    model_used: Optional[str] = None
    language: Optional[str] = None
    synthesized_at: Optional[str] = None
    watermark_label: str = "AI-Generated Voice Recreation - Memorial Simulation Only"
    authorized_by: Optional[str] = None


class VoiceSynthesisRequest(BaseModel):
    """Request payload to synthesize remembrance speech."""

    language: Literal["en", "es", "hi", "fr", "de", "it", "pt"] = "es"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    consent: Optional[VoiceConsentRecord] = None
    authorized_by: Optional[str] = None
    confirmed_permission: Optional[bool] = None
    engine: Optional[str] = None

    @model_validator(mode="after")
    def resolve_consent(self) -> "VoiceSynthesisRequest":
        if self.consent is None:
            if not self.authorized_by or not self.confirmed_permission:
                raise ValueError("Both authorized_by and confirmed_permission=True are required.")
            self.consent = VoiceConsentRecord(
                authorized_by=self.authorized_by,
                confirmed_permission=self.confirmed_permission,
            )
        return self


class OfrendaCreate(BaseModel):
    """Payload to create a new ofrenda."""

    name: str = Field(..., min_length=1, max_length=80)
    relationship: Optional[str] = Field(None, max_length=40)
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    language: Literal["en", "es", "hi"] = "es"
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
    language: Optional[Literal["en", "es", "hi"]] = None
    foods: Optional[List[str]] = Field(None, max_length=12)
    drinks: Optional[List[str]] = Field(None, max_length=6)
    songs: Optional[List[str]] = Field(None, max_length=6)
    objects: Optional[List[str]] = Field(None, max_length=8)
    story_text: Optional[str] = Field(None, max_length=5000)
    transcript: Optional[str] = None
    remembrance: Optional[str] = None
    generated_by: Optional[str] = None
    model_used: Optional[str] = None
    voice_profile: Optional[VoiceProfileMetadata] = None

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
    language: Literal["en", "es", "hi"] = "es"
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
    voice_profile: Optional[VoiceProfileMetadata] = None


class OfrendaSummary(BaseModel):
    """Summary of an ofrenda for listings."""

    id: str
    name: str
    created_at: str
    relationship: Optional[str] = None
    photo: Optional[str] = None
    has_voice: bool = False


class GenerateRequest(BaseModel):
    """Optional payload for remembrance generation."""

    model: Optional[str] = None
