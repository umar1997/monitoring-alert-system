import re
import json

def postprocess_drug_db(data_str):
    json_matches = re.findall(r'```json\n(.*?)\n```', data_str, re.DOTALL)
    json_objects = [json.loads(match) for match in json_matches]

    def convert_to_sql_schema(drug):
        return {
            "drug_id": int(drug["drug_id"]) if drug["drug_id"] else None,
            "drug_name": drug["drug_name"],
            "visit_occurrence_id": int(drug["visit_occurrence_id"]) if drug["visit_occurrence_id"] else None,
            "drug_strength": drug["drug_strength"],
            "frequency": drug["frequency"],
            "duration_in_days": int(drug["duration_in_days"]) if drug["duration_in_days"] else 0,
            "drug_form": drug["drug_form"],
            "quantity": int(drug["quantity"]) if drug["quantity"] else 0,
            "instructions": drug["instructions"],
            "person_id": int(drug["person_id"]) if drug["person_id"] else None,
            "refill_in_days": int(drug["duration_in_days"]) if drug["duration_in_days"] else 0,  # Match refill_in_days to duration_in_days
            "prescription_id": int(drug["prescription_id"]) if drug["prescription_id"] else None,
            "schedule_status": 0  # Default as per SQL schema
        }

    final_json = convert_to_sql_schema(json_objects[-1])
    return final_json