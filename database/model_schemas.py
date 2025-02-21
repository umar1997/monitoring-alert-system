
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey


Base = declarative_base()

class Drug(Base):
    __tablename__ = 'drugs'

    drug_id = Column(Integer, primary_key=True, index=True)
    drug_name = Column(String, index=True)
    visit_occurrence_id = Column(Integer)
    drug_strength = Column(String)
    frequency = Column(String)
    duration_in_days = Column(Integer)
    drug_form = Column(String)
    quantity = Column(Integer)
    instructions = Column(String)
    person_id = Column(Integer)
    refill_in_days = Column(Integer)
    prescription_id = Column(Integer)

class PatientDrugRecommendation(Base):
    __tablename__ = 'patient_drug_recommendation'

    visit_occurrence_id = Column(Integer, primary_key=True, index=True)
    dietary_recommendation = Column(String)
    side_effects = Column(String)
    drug_purpose = Column(String(255))
    drug_consumption_pattern = Column(String(255))
    person_id = Column(Integer, index=True)

class Prescription(Base):
    __tablename__ = "prescription"

    id = Column(Integer, primary_key=True, index=True)
    visit_occurrence_id = Column(Integer, ForeignKey("visit_occurrence.visit_occurrence_id"))
    person_id = Column(Integer, ForeignKey("patient.person_id"))
    file_content = Column(LargeBinary)

    # Relationships (if needed)
    # visit_occurrence = relationship("VisitOccurrence", back_populates="prescriptions")
    # person = relationship("Patient", back_populates="prescriptions")


# Pydantic model for the request body
class PatientDrugRecommendationCreate(BaseModel):
    visit_occurrence_id: int
    dietary_recommendation: str
    side_effects: str
    drug_purpose: str
    drug_consumption_pattern: str
    person_id: int


class DrugCreate(BaseModel):
    drug_name: str
    visit_occurrence_id: int
    drug_strength: str
    frequency: str
    duration_in_days: int
    drug_form: str
    quantity: int
    instructions: str
    person_id: int
    refill_in_days: int
    prescription_id: int