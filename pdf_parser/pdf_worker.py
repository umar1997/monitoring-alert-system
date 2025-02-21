import os
import time
import logging
import argparse

import base64
import hashlib
import aiofiles
import asyncio

from fastapi import UploadFile
from io import BytesIO

import uvicorn
from fastapi import (
    FastAPI, 
    APIRouter, 
    Request, 
    BackgroundTasks,
    UploadFile, 
    File, 
    Body, 
    Form
)
from fastapi.responses import StreamingResponse, JSONResponse

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from pdf_parser.helpers import calculate_time, remove_pdf_file
from pdf_parser.azure_parser import DocumentParser

class ParserWorker:
    def __init__(
        self,
        parser_type: str,
        azure_version: str,
        cwd: str
    ):
        global worker
        self.parser_type = parser_type
        self.azure_version = azure_version
        self.cwd = cwd

    async def execute_parser(self, file_path):

        parsed_text = {}
        
        print(f'{"#"*30}\nAZURE PARSER\n{"#"*30}\n')
        parser = DocumentParser(file_path, self.azure_version)
        parsed_text = await parser.run_parser()
            
                
        remove_pdf_file(file_path)
        return {"response": parsed_text}

    async def write_bytes_to_pdfs(self, file, pdf_files_path, hash_code):
        pdf_bytes = file.file.read()
        # pdf_bytes = file
        filename = f"{hash_code}.pdf"
        file_path = os.path.join(pdf_files_path, str(hash_code) + ".pdf")
        files_info = { 
            "hash_code": str(hash_code), 
            "filepath": file_path, 
            "filename": filename
        }
        print(f"Processing PDF: {filename}\nPDF Info: {files_info}")

        async with aiofiles.open(file_path, "wb") as binary_file:
            await binary_file.write(pdf_bytes)
        
        return files_info

    def generate_hash_key(self, pdf_bytes):
        encoded_string = base64.b64encode(pdf_bytes).decode('utf-8')
        hasher = hashlib.sha256()
        hasher.update(encoded_string.encode('utf-8'))
        hash_code = hasher.hexdigest()
        return hash_code
    
    def extract_text_and_tables(self, pdf_data: dict):
        response = pdf_data.get("response", {})
        total_pages = response.get("total_pages", 0)
        extracted_content = []

        for page_num in range(1, total_pages + 1):
            page_data = response.get(str(page_num), {})
            text = page_data.get("text", "").strip()
            tables = page_data.get("tables", [])

            page_content = f"Page {page_num}:\n"
            page_content += f"Text: {text if text else ''}\n"

            for table in tables:
                page_content += f"Table:\n{table}\n"

            extracted_content.append(page_content)

        return "\n\n".join(extracted_content)
    
    async def execute_parse_text(self, file: bytes):
        hash_code = self.generate_hash_key(file)
        filename = str(hash_code) + ".pdf"
        pdf_bytes = UploadFile(filename=filename, file=BytesIO(file))
        pdf_file_path = os.environ.get('PDF_FILES_PATH', "/rag_app/pdf_files/")
        os.makedirs(pdf_file_path, exist_ok=True)
        file_info = await self.write_bytes_to_pdfs(pdf_bytes, pdf_file_path, hash_code)
        pdf_data = await self.execute_parser(file_info['filepath'])
        output = self.extract_text_and_tables(pdf_data)
        return output
