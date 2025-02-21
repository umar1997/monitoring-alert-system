import os
import re
from pdf_parser.helpers import Timer
from pdf_parser.table_utils import generate_markdown_table

import io
import PyPDF2
import asyncio
import aiofiles
from tempfile import NamedTemporaryFile

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

# For Version 3
from azure.ai.formrecognizer import DocumentAnalysisClient

# For Version 4
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult


class DocumentParser:
    def __init__(self, filepath, version):
        self.filepath = filepath
        self.pdf_path = os.environ.get("PDF_FILES_PATH", "/rag_app/pdf_files/")
        self.image_path = os.environ.get("PDF_IMAGES_PATH", "/rag_app/images_files/")

        self.file_name = self.get_file_name(filepath)
        self.file_pdf_path = os.path.join(self.pdf_path, self.file_name)
        self.file_image_path = os.path.join(self.image_path, self.file_name.replace(".pdf", ""))

        self.timer = Timer()

        self.VERSION = version
        self.version_dict = self.version_dictionary()
        if self.VERSION == "V3":
            self.endpoint = os.environ.get('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT_V3')
            self.key = os.environ.get('AZURE_DOCUMENT_INTELLIGENCE_KEY_V3')
        else:
            self.endpoint = os.environ.get('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT_V4')
            self.key = os.environ.get('AZURE_DOCUMENT_INTELLIGENCE_KEY_V4')

        print(f"PDF File Path: {self.file_pdf_path}")
        print(f"Image File Path: {self.file_image_path}")

    def version_dictionary(self,):
        version_dict = {
            "V3": {
                "pageNumber": "page_number",
                "boundingRegions": "bounding_regions",
                "rowCount": "row_count",
                "columnCount": "column_count",
                "rowIndex": "row_index",
                "columnIndex": "column_index"
            },
            "V4": {
                "pageNumber": "pageNumber",
                "boundingRegions": "boundingRegions",
                "rowCount": "rowCount",
                "columnCount": "columnCount",
                "rowIndex": "rowIndex",
                "columnIndex": "columnIndex"
            }
        }
        return version_dict

    async def analyze_document(self,):

        if self.VERSION == "V4":
            document_intelligence_client = DocumentIntelligenceClient(
                endpoint=self.endpoint, credential=AzureKeyCredential(self.key)
            )
            page_readers, num_pages = await self.split_pdf_to_buffered_readers(self.file_pdf_path)
            results = await self.analyze_pages(document_intelligence_client, page_readers)
            return results
        elif self.VERSION == "V3":
            document_intelligence_client = DocumentAnalysisClient(
                endpoint=self.endpoint, credential=AzureKeyCredential(self.key)
            )
            page_readers, num_pages = await self.split_pdf_to_buffered_readers(self.file_pdf_path)
            results = await self.analyze_pages(document_intelligence_client, page_readers)
            return results
            # with open(self.file_pdf_path, "rb") as f:
            #     poller =  await asyncio.to_thread(document_intelligence_client.begin_analyze_document,
            #         "prebuilt-layout", document=f
            #     )
            # result = poller.result()
            # return result.to_dict()
        
    async def analyze_pages(self, document_intelligence_client, page_readers):
        async def analyze_single_page(f):
            if self.VERSION == "V4":
                poller = await asyncio.to_thread(document_intelligence_client.begin_analyze_document, "prebuilt-layout", analyze_request=f, content_type="application/octet-stream")
                result = poller.result()
                return result
            else:
                poller = await asyncio.to_thread(document_intelligence_client.begin_analyze_document, "prebuilt-layout", document=f)
                result = poller.result()
                return result.to_dict()
            

        tasks = [analyze_single_page(f) for f in page_readers]
        results = await asyncio.gather(*tasks)
        return results
        
    async def split_pdf_to_buffered_readers(self, pdf_path):
        async with aiofiles.open(pdf_path, "rb") as pdf_file:
            pdf_bytes = await pdf_file.read()

        pdf_stream = io.BytesIO(pdf_bytes)
        reader = await asyncio.to_thread(PyPDF2.PdfReader, pdf_stream)
        num_pages = len(reader.pages)

        async def process_page(page_num):
            with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[page_num])
                writer.write(temp_pdf)

            buffered_reader = open(temp_pdf.name, "rb")
            def cleanup():
                os.remove(temp_pdf.name)
            buffered_reader.close = lambda: (buffered_reader.close(), cleanup())
            return buffered_reader

        page_readers = await asyncio.gather(*(process_page(page_num) for page_num in range(num_pages)))        
        return page_readers, num_pages

    def get_file_name(self, filepath):
        return filepath[filepath.rfind("/")+1:]
    
    def parsed_figures_and_captions(self, data, pages_obj, page_number):
        figure_elements, caption_elements = [], []
        if 'figures' in data:
            for figure in data['figures']:
                if 'elements' in figure:
                    for elem in figure['elements']:
                        figure_elements.append(int(re.search(r'\d+', elem).group()))
                if 'caption' in figure:
                    for elem in figure['caption']['elements']:
                        caption_elements.append(int(re.search(r'\d+', elem).group()))
                        page_number = page_number # For Split
                        pages_obj[page_number]["images"].append(figure['caption']["content"])
            
            filtered_figure_elements = [item for item in figure_elements if item not in caption_elements]
        else:
            filtered_figure_elements = []
        return pages_obj, filtered_figure_elements
    
    def parsed_tables(self, data, pages_obj, page_number):
        table_elements = []
        if 'tables' in data:
            for table in data['tables']:
                cell_data = []
                total_rows = table[self.version_dict[self.VERSION]['rowCount']]
                total_columns = table[self.version_dict[self.VERSION]['columnCount']]
                if 'cells' in table:
                    for cell in table["cells"]:
                        cell_data.append((cell[self.version_dict[self.VERSION]["rowIndex"]],cell[self.version_dict[self.VERSION]["columnIndex"]],cell["content"]))
                        if 'elements' in cell:
                            for elem in cell['elements']:
                                table_elements.append(int(re.search(r'\d+', elem).group()))
                    table_markdown = generate_markdown_table(total_columns, total_rows, cell_data)
                    pages_obj[page_number]["tables"].append(table_markdown)

        return pages_obj, table_elements

    async def init_parser(self,):
        doc = {}
        data = await self.analyze_document()
        doc['total_pages'] = len(data)
        concatenated_elements = {}
        pages_obj = {str(page): {"text": "", "tables": [], "images": []} for page in range(1, doc['total_pages'] + 1)}
        for idx, page_data in enumerate(data):
            page_number = str(idx + 1)
            pages_obj, filtered_figure_elements = self.parsed_figures_and_captions(page_data, pages_obj, page_number) if self.VERSION == "V4" else (pages_obj, [])
            # pages_obj, table_elements = self.parsed_tables(page_data, pages_obj, page_number) if self.VERSION == "V4" else (pages_obj, [])
            pages_obj, table_elements = self.parsed_tables(page_data, pages_obj, page_number)
            concatenated_elements[page_number] = set(filtered_figure_elements + table_elements)
            
        return doc, data, pages_obj, concatenated_elements

    def parse_text(self, doc, data, pages_obj, concatenated_elements):
        title_found = False
        for index, page_data in enumerate(data):
            page = str(index + 1)  # For Split
            if "paragraphs" in page_data:
                for idx, paragraph in enumerate(page_data["paragraphs"]):
                    if idx in concatenated_elements[page]:
                        continue
                    if 'role' in paragraph and paragraph['role'] and paragraph['role'] == 'title' and not title_found: 
                        doc["title"] = paragraph["content"]

                    if 'role' in paragraph and paragraph['role']:
                        start_text = "\n\n" if pages_obj[page]["text"] else ""
                        if paragraph['role'].lower() == 'title':
                            paragraph['role'], title_found = ('HEADING', title_found) if title_found else (paragraph['role'], True)
                        
                        pages_obj[page]["text"] += start_text + f"{paragraph['role'].title()}: {paragraph['content']}\n"
                    else: 
                        pages_obj[page]["text"] += f" {paragraph['content']}"
                pages_obj[page]["text"] = pages_obj[page]["text"].strip()
            else:
                pages_obj[page]["text"] = ""
        for k, v in pages_obj.items():
            doc[k] = v
        return doc

    async def run_parser(self,):
        with self.timer("INIT PARSER"):
            doc, data, pages_obj, elements = await self.init_parser()
        with self.timer("PARSE TEXT"):
            result = self.parse_text(doc, data, pages_obj, elements)
        if result:
            print("*"*50)
            print(f"PDF Title: {result['title'] if 'title' in result else ''}")
            print(f"Total Pages: {result['total_pages'] if 'total_pages' in result else 0}")
            print(f"Result Keys: {result.keys()}")
            print(f"Page 1: {result['1'] if '1' in result else 0}")

            print("*"*50)
        with self.timer("RETURN"):
            return result