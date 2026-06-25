from sqlalchemy import Column, String, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.common.base_model import BaseModel


class Industry(BaseModel):
    __tablename__ = "industries"

    industry_name = Column(String(200), nullable=False, unique=True)
    parent_industry_id = Column(UUID(as_uuid=True), ForeignKey("industries.id"), nullable=True)
    description = Column(Text)
    sic_code = Column(String(10))
    naics_code = Column(String(10))

    parent = relationship("Industry", remote_side="Industry.id", backref="children")
    companies = relationship("Company", back_populates="industry")


class Country(BaseModel):
    __tablename__ = "countries"

    name = Column(String(100), nullable=False, unique=True)
    iso2 = Column(String(2), unique=True, nullable=False)
    iso3 = Column(String(3), unique=True, nullable=False)
    phone_code = Column(String(10))
    currency = Column(String(10))
    continent = Column(String(50))

    states = relationship("State", back_populates="country")
    companies = relationship("Company", back_populates="country")
    contacts = relationship("Contact", back_populates="country")


class State(BaseModel):
    __tablename__ = "states"

    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10))

    country = relationship("Country", back_populates="states")
    cities = relationship("City", back_populates="state")


class City(BaseModel):
    __tablename__ = "cities"

    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id", ondelete="CASCADE"), nullable=True, index=True)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))

    state = relationship("State", back_populates="cities")


class Technology(BaseModel):
    __tablename__ = "technologies"

    technology_name = Column(String(200), nullable=False, unique=True)
    category = Column(String(100))
    vendor = Column(String(200))
    description = Column(Text)
    logo_url = Column(String(500))
    website = Column(String(255))

    companies = relationship("Company", secondary="company_technologies", back_populates="technologies")
