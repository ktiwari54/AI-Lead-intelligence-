import uuid
from sqlalchemy import String, ForeignKey, Index, Numeric, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class Industry(BaseModel):
    __tablename__ = "industries"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("industries.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(String(1000))
    naics_code: Mapped[str | None] = mapped_column(String(10))
    sic_code: Mapped[str | None] = mapped_column(String(10))

    parent: Mapped["Industry | None"] = relationship("Industry", remote_side="Industry.id")
    children: Mapped[list["Industry"]] = relationship("Industry", back_populates="parent")
    companies: Mapped[list["Company"]] = relationship("Company", back_populates="industry")


class Country(BaseModel):
    __tablename__ = "countries"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    iso2: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    iso3: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    phone_code: Mapped[str | None] = mapped_column(String(20))
    continent: Mapped[str | None] = mapped_column(String(50))
    currency_code: Mapped[str | None] = mapped_column(String(10))

    __table_args__ = (
        Index("ix_countries_iso2", "iso2"),
        Index("ix_countries_name", "name"),
    )

    states: Mapped[list["State"]] = relationship("State", back_populates="country")


class State(BaseModel):
    __tablename__ = "states"

    country_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20))

    __table_args__ = (Index("ix_states_country_id", "country_id"),)

    country: Mapped["Country"] = relationship("Country", back_populates="states")
    cities: Mapped[list["City"]] = relationship("City", back_populates="state")


class City(BaseModel):
    __tablename__ = "cities"

    state_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("states.id"), nullable=True
    )
    country_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7))

    __table_args__ = (
        Index("ix_cities_state_id", "state_id"),
        Index("ix_cities_country_id", "country_id"),
        Index("ix_cities_name", "name"),
    )

    state: Mapped["State | None"] = relationship("State", back_populates="cities")


class Technology(BaseModel):
    __tablename__ = "technologies"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    vendor: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    website: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (
        Index("ix_technologies_name", "name"),
        Index("ix_technologies_category", "category"),
    )

    company_technologies: Mapped[list["CompanyTechnology"]] = relationship(
        "CompanyTechnology", back_populates="technology"
    )
