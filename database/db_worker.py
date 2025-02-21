from typing import Dict, Optional
from fastapi import HTTPException


def prescription_file_content(db, prescription_id: int):
    with db.cursor() as cursor:
        cursor.execute("SELECT file_content FROM prescription WHERE id = %s", (prescription_id,))
        result = cursor.fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return result[0]



def insert_drug_record(db, prescription_id, person_id, visit_occurrence_id, drug_data: Dict):
    query = """
        INSERT INTO drugs (
            drug_name, visit_occurrence_id, drug_strength, frequency, 
            duration_in_days, drug_form, quantity, instructions, person_id, 
            refill_in_days, prescription_id, schedule_status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        # drug_data.get("drug_id"),  # INT (Can be None)
        drug_data["drug_name"],  # NVARCHAR(255) (Required)
        visit_occurrence_id,  # INT (Can be None)
        drug_data["drug_strength"],  # NVARCHAR(255) (Required)
        drug_data["frequency"],  # NVARCHAR(255) (Required)
        int(drug_data["duration_in_days"]),  # INT
        drug_data["drug_form"],  # NVARCHAR(255) (Required)
        int(drug_data["quantity"]),  # INT
        drug_data["instructions"],  # NVARCHAR(MAX)
        person_id,  # INT (Can be None)
        int(drug_data["refill_in_days"]),  # INT
        prescription_id,  # INT (Can be None)
        bool(drug_data.get("schedule_status", 0))  # BIT (Defaults to 0)
    )

    try:
        with db.cursor() as cursor:
            cursor.execute(query, values)
            db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def insert_patient_drug_recommendation(db, recommendation_data: Dict):
    query = """
        INSERT INTO patient_drug_recommendation (
            visit_occurrence_id, dietary_recommendation, side_effects, 
            drug_purpose, drug_consumption_pattern, person_id, prescription_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        recommendation_data["visit_occurrence_id"],  # INT (Required)
        recommendation_data["dietary_recommendation"],  # NVARCHAR(MAX) (Required)
        recommendation_data["side_effects"],  # NVARCHAR(MAX) (Required)
        recommendation_data["drug_purpose"],  # NVARCHAR(255) (Required)
        recommendation_data["drug_consumption_pattern"],  # NVARCHAR(255) (Required)
        recommendation_data["person_id"],  # INT (Required)
        recommendation_data["prescription_id"]  # INT (Can be None)
    )

    try:
        with db.cursor() as cursor:
            cursor.execute(query, values)
            db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")