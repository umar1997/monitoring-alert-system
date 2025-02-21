import os
import logging

import uvicorn
import asyncio
import pymssql
import argparse


from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI, UploadFile, File 
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from utilities.tags import docs_meta_tags

worker = None
app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="DoseSense API",
        version="1.0",
        description="This is the official documentation for DoseSense",
        routes=app.routes,
    )
    openapi_schema['tags'] = docs_meta_tags()
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# SQL Server connection details
AZURE_SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
AZURE_SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE")
AZURE_SQL_USERNAME = os.getenv("AZURE_SQL_USERNAME")
AZURE_SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")

# Function to establish a connection using pymssql
def get_db_connection():
    try:
        conn = pymssql.connect(
            server=AZURE_SQL_SERVER,
            user=AZURE_SQL_USERNAME,
            password=AZURE_SQL_PASSWORD,
            database=AZURE_SQL_DATABASE
        )
        print("✅ Connected to Azure SQL Database using pymssql")
        return conn
    except pymssql.Error as e:
        print(f"❌ Connection failed: {e}")
        return None

@app.on_event("startup")
def startup_db_client():
    conn = get_db_connection()
    if conn:
        app.state.db = conn  # Store connection in app state
        with conn.cursor() as cursor:
            cursor.execute("SELECT @@VERSION;")
            row = cursor.fetchone()
            while row:
                print(row[0])
                row = cursor.fetchone()

@app.on_event("shutdown")
def shutdown_db_client():
    conn = app.state.db
    if conn:
        conn.close()
        print("🔌 Database connection closed")

@app.get("/", tags=["Default"])
async def index():
    return {"message": "Backend Server Running"}

@app.get("/test-db")
def test_db():
    conn = app.state.db
    if not conn:
        return {"Error": "Database connection is not available"}

    with conn.cursor() as cursor:
        cursor.execute("SELECT TOP 1 name FROM sys.tables;")
        row = cursor.fetchone()
        return {"table_name": row[0] if row else "No tables found"}



from pydantic import BaseModel, Field

from web.web_worker import WebWorker
from pdf_parser.pdf_worker import ParserWorker
from llm.llm_worker import LLMGenerator
from database.db_worker import (
    insert_drug_record,
    prescription_file_content,
    insert_patient_drug_recommendation
)
from database.db_processing import (
    postprocess_drug_db
)
from web.application_utils.schema_models import WebSearchModel

class PrescriptionRequestModel(BaseModel):
    personId: int = Field(default=1)
    visitOccurrenceId: int = Field(default=1)
    prescriptionId: int = Field(default=4)


class BaseWorker:
    def __init__(
        self,
        current_work_dir: str,
        parser_type: str,
        azure_version: str
    ):
        global worker
        self.web_worker = WebWorker(cwd=current_work_dir)
        self.pdf_worker = ParserWorker(parser_type=parser_type, azure_version=azure_version, cwd=current_work_dir)
        self.llm_worker = LLMGenerator(cwd=current_work_dir)
        
        worker = self
    
    async def fetch_and_process(self, drug_name, query):
        output = await self.web_worker.execute_web_retrieve(WebSearchModel(query_text=query))
        query_and_chunks, urls_string = self.web_worker.chunks_and_urls(output)
        response = await self.llm_worker.execute_llm(query_and_chunks, "clean_scraped")
        return response + urls_string

    async def process_drug_info(self, drug_name):
        side_effects_task = self.fetch_and_process(drug_name, f"What are the side effects of {drug_name}?")
        drug_purpose_task = self.fetch_and_process(drug_name, f"What is the purpose of {drug_name}?")
        drug_recommendation_task = self.fetch_and_process(drug_name, f"What is the consumption recommendation for {drug_name}?")
        diet_recommendation_task = self.fetch_and_process(drug_name, f"What is the diet recommendation while taking {drug_name}?")

        side_effects, drug_purpose, drug_recommendation, diet_recommendation = await asyncio.gather(
            side_effects_task, drug_purpose_task, drug_recommendation_task, diet_recommendation_task
        )

        return side_effects, drug_purpose, drug_recommendation, diet_recommendation

    async def execute_worker(self, conn, request):
        prescription_id = request.prescriptionId
        visit_occurrence_id = request.visitOccurrenceId
        person_id = request.personId
        try:
            file_content = prescription_file_content(conn, int(prescription_id))
            output = await self.pdf_worker.execute_parse_text(file_content)
            output = await self.llm_worker.execute_llm(output, "extract_info")
            drug_table = postprocess_drug_db(output)
            
            insert_drug_record(conn, prescription_id, person_id, visit_occurrence_id, drug_table)
            drug_name = drug_table.get("drug_name")
            
            recommendation_data = {}
            recommendation_data["side_effects"], recommendation_data["drug_purpose"], recommendation_data["drug_consumption_pattern"], recommendation_data["dietary_recommendation"] = await self.process_drug_info(drug_name)
            recommendation_data["person_id"] = person_id
            recommendation_data["prescription_id"] = prescription_id
            recommendation_data["visit_occurrence_id"] = visit_occurrence_id
            insert_patient_drug_recommendation(conn, recommendation_data)
            output = {
                "drug_table": drug_table,
                "recommendation_data": recommendation_data
            }
            return output
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid prescription ID format")


@app.get("/", tags=["Default"])
async def index():
    return {"Message": "Backend Server Running"}

@app.post("/run-worker", tags=["Default"])
async def fetch_prescription_file(request: PrescriptionRequestModel):
    conn = app.state.db
    result = await worker.execute_worker(conn, request)

    return JSONResponse(result)

if __name__ == "__main__":
    # Argument parser for host and port
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for the server")
    parser.add_argument("--port", type=int, default=18080, help="Port for the server")

    parser.add_argument("--parser_type", type=str, default="azure")
    parser.add_argument( "--azure_version", type=str, default="V4")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    current_work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    worker = BaseWorker(
        current_work_dir,
        args.parser_type,
        args.azure_version
    )

    uvicorn.run(app, host=args.host, port=args.port, log_level=logging.INFO)