from __future__ import annotations

from datetime import date as Date
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator, field_validator


# ── Analytics & Coverage Events ───────────────────────
DataMode = Literal["live", "fixture", "missing"]
CoverageStatus = Literal["draft_only", "verified", "estimated", "unsupported"]
DecisionStatus = Literal["recommended", "needs_revision", "insufficient_data"]
DecisionConfidence = Literal["high", "medium", "low", "insufficient"]
AnalyticsEventType = Literal["plan_completed", "plan_edited", "decision_blocked", "recommendation_accepted", "recommendation_rejected"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProviderRecord(BaseModel):
    provider: str
    retrieved_at: datetime = Field(default_factory=utc_now)
    data_mode: DataMode = "live"
    assumptions: list[str] = Field(default_factory=list)


class TripPlan(BaseModel):
    origin: str | None = None
    destination: str | None = None
    departure_date: Date | None = None
    return_date: Date | None = None
    days: int | None = Field(default=None, ge=1, le=30)
    nights: int | None = Field(default=None, ge=0)
    travelers: int = Field(default=1, ge=1, le=20)
    budget_total: float | None = Field(default=None, ge=0)
    budget_per_person: float | None = Field(default=None, ge=0)
    currency: str = "VND"
    comfort_level: Literal["budget", "medium", "comfortable"] = "medium"
    priority: Literal["cheapest", "less_travel", "comfortable"] = "cheapest"
    preferences: list[str] = Field(default_factory=list)
    constraints: dict = Field(default_factory=dict)
    trip_type: str | None = None
    must_have: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    special_requirements: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    goal: str = ""
    version: int = 1

    @model_validator(mode="after")
    def derive_fields(self) -> "TripPlan":
        if self.departure_date and self.return_date:
            delta = (self.return_date - self.departure_date).days
            if delta < 0:
                raise ValueError("return_date must not be before departure_date")
            self.nights = delta
            self.days = delta + 1
        elif self.days and self.nights is None:
            self.nights = max(self.days - 1, 0)
        if self.budget_total is None and self.budget_per_person is not None:
            self.budget_total = self.budget_per_person * self.travelers
        if self.budget_per_person is None and self.budget_total is not None:
            self.budget_per_person = self.budget_total / self.travelers
        return self

    def missing_required_fields(self) -> list[str]:
        missing: list[str] = []
        if not self.destination:
            missing.append("destination")
        if not self.days and not (self.departure_date and self.return_date):
            missing.append("days_or_date_range")
        if not self.budget_total and not self.budget_per_person:
            missing.append("budget")
        if not self.preferences:
            missing.append("preferences")
        if not self.comfort_level:
            missing.append("comfort_level")
        return missing


class FlightOption(ProviderRecord):
    id: str
    airline: str
    departure_time: str = ""
    arrival_time: str = ""
    duration_minutes: int = Field(default=0, ge=0)
    stops: int = Field(default=0, ge=0)
    price: float = Field(ge=0, description="Price per traveler")
    price_scope: Literal["round_trip_per_traveler", "one_way_per_traveler"] = "one_way_per_traveler"
    currency: str = "VND"
    booking_url: str | None = None
    tradeoffs: list[str] = Field(default_factory=list)


class HotelOption(ProviderRecord):
    id: str
    name: str
    area: str = ""
    price_per_night: float = Field(ge=0)
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int = Field(default=0, ge=0)
    distance_to_center_km: float | None = Field(default=None, ge=0)
    booking_url: str | None = None
    amenities: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    lat: float | None = None
    lng: float | None = None
    provider_place_id: str | None = None


class PlaceOption(ProviderRecord):
    id: str
    name: str
    category: str
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int = Field(default=0, ge=0)
    lat: float | None = None
    lng: float | None = None
    estimated_visit_minutes: int = Field(default=90, ge=0)
    estimated_cost: float = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)
    priority: Literal["must_go", "recommended", "optional"] = "recommended"
    
    # UX Plan Sprint 1 Additions
    address: str = ""
    area: str = ""
    provider_place_id: str | None = None
    maps_url: str | None = None
    place_match_status: Literal["verified", "unverified", "fixture", "missing"] = "missing"
    place_match_confidence: Literal["high", "medium", "low"] = "low"

    @model_validator(mode="after")
    def validate_place_identity(self):
        if self.provider_place_id:
            self.place_match_status = "verified"
            self.place_match_confidence = "high"
        elif getattr(self, "data_mode", "") == "fixture":
            self.place_match_status = "fixture"
            self.place_match_confidence = "low"
        elif self.lat and self.lng and self.place_match_status == "missing":
            self.place_match_status = "unverified"
            self.place_match_confidence = "medium"
        return self


class RouteSegment(ProviderRecord):
    from_place_id: str
    to_place_id: str
    mode: str = "driving"
    distance_km: float = Field(default=0, ge=0)
    duration_minutes: int = Field(default=0, ge=0)


class WeatherForecast(ProviderRecord):
    date: Date
    location: str
    temperature_min: float | None = None
    temperature_max: float | None = None
    rain_probability: float = Field(default=0, ge=0, le=1)
    summary: str = ""
    activity_impact: list[str] = Field(default_factory=list)


class ReviewSummary(ProviderRecord):
    target_id: str
    positive_points: list[str] = Field(default_factory=list)
    negative_points: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"


class DecisionEvidence(BaseModel):
    type: Literal["warning", "info", "success"]
    rule: str
    observed_value: str
    threshold: str | None = None
    recommendation: str | None = None
    target_id: str | None = None
    suggested_actions: list[str] = Field(default_factory=list)


class ItineraryItem(BaseModel):
    place_id: str | None = None
    title: str
    category: str = ""
    outdoor: bool = False
    estimated_cost: float = 0
    estimated_visit_minutes: int = 90
    maps_url: str | None = None
    confidence: Literal["verified", "estimated", "unverified", "fixture", "missing"] = "verified"


class ItineraryLeg(BaseModel):
    from_place_id: str
    from_label: str
    to_place_id: str
    to_label: str
    mode: str = "driving"
    distance_km: float | None = None
    duration_minutes: int | None = None
    provider: str = "fallback"
    data_mode: Literal["live", "fixture", "missing"] = "missing"
    confidence: Literal["verified", "estimated", "unverified"] = "unverified"
    directions_url: str | None = None

class ItineraryDay(BaseModel):
    day: int = Field(ge=1)
    date: Date | None = None
    title: str = ""
    items: list[ItineraryItem] = Field(default_factory=list)
    travel_minutes: int = Field(default=0, ge=0)
    evidence: list[DecisionEvidence] = Field(default_factory=list)
    route_legs: list[ItineraryLeg] = Field(default_factory=list)
    total_visit_minutes: int = Field(default=0, ge=0)
    area_summary: str = ""
    route_status: Literal["verified", "unverified", "estimated"] = "unverified"


class CostBreakdown(BaseModel):
    flights: float = 0
    hotels: float = 0
    food: float = 0
    local_transport: float = 0
    tickets: float = 0
    buffer: float = 0

    @property
    def total(self) -> float:
        return sum(self.model_dump().values())


class Risk(BaseModel):
    type: str
    severity: Literal["low", "medium", "high"]
    message: str
    recommendation: str | None = None
    target_day: int | None = None
    target_place_id: str | None = None
    target_route_id: str | None = None
    suggested_action: str | None = None


class RankedOption(BaseModel):
    id: Literal["cheapest", "balanced", "comfortable"]
    flight_id: str | None = None
    hotel_id: str | None = None
    total_cost: float = 0
    cost_score: float = 0
    feasibility_score: float = 0
    comfort_score: float = 0
    value_score: float = 0
    feasibility_status: Literal["Khả thi", "Khả thi có điều kiện", "Cần chỉnh sửa", "Không đủ dữ liệu"] = "Không đủ dữ liệu"
    comfort_status: str = ""
    cost_breakdown: CostBreakdown = Field(default_factory=CostBreakdown)
    tradeoffs: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class DecisionInput(BaseModel):
    trip_plan: TripPlan
    flight_options: list[FlightOption] = Field(default_factory=list)
    hotel_options: list[HotelOption] = Field(default_factory=list)
    place_options: list[PlaceOption] = Field(default_factory=list)
    route_segments: list[RouteSegment] = Field(default_factory=list)
    weather_forecasts: list[WeatherForecast] = Field(default_factory=list)
    review_summaries: list[ReviewSummary] = Field(default_factory=list)
    itinerary: list[ItineraryDay] = Field(default_factory=list)
    cost_rules: dict[str, float] = Field(default_factory=dict)


class DecisionOutput(BaseModel):
    recommended_option: str | None = None
    budget_status: Literal["under_budget", "near_limit", "slightly_over", "over_budget", "unknown"]
    total_cost: float
    total_cost_per_person: float
    budget_delta: float | None = None
    feasibility_score: float
    comfort_score: float
    value_score: float
    cost_breakdown: CostBreakdown
    options: list[RankedOption] = Field(default_factory=list)
    itinerary: list[ItineraryDay] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    evidence: list[DecisionEvidence] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    why_recommended: list[str] = Field(default_factory=list)
    booking_links: list[str] = Field(default_factory=list)
    # Sprint 1: Coverage & trust fields
    coverage_status: CoverageStatus = "draft_only"
    decision_status: DecisionStatus = "insufficient_data"
    confidence: DecisionConfidence = "insufficient"
    blocking_reasons: list[str] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    rule_version: str = "v1.0"
    data_freshness: dict[str, str] = Field(default_factory=dict)
