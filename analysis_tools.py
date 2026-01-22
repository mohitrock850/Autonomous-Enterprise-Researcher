import os
import base64
import requests
import fitz  
from crewai.tools import BaseTool
from langchain_experimental.tools import PythonREPLTool

# --- 1. Code Interpreter ---
class CodeInterpreterTool(BaseTool):
    name: str = "Code Interpreter"
    description: str = "Useful for executing Python code to analyze data. Input: Python code string."

    def _run(self, code: str) -> str:
        repl = PythonREPLTool()
        try:
            clean_code = code.replace("```python", "").replace("```", "").strip()
            return repl.run(clean_code)
        except Exception as e:
            return f"Error: {e}"

# --- 2. File Lister  ---
class FileListerTool(BaseTool):
    name: str = "List PDF Files"
    description: str = "Useful to see what PDF files are available in the 'data' directory. Input: Just pass the word 'check'."

    def _run(self, query: str) -> str:
        data_dir = "data"
        if not os.path.exists(data_dir):
            return "Error: 'data' directory not found."
        
        files = [f for f in os.listdir(data_dir) if f.lower().endswith('.pdf')]
        if not files:
            return "No PDF files found in 'data' directory."
        return f"Available PDFs: {', '.join(files)}"

# --- 3. PDF Image Extractor ---
class PDFImageExtractorTool(BaseTool):
    name: str = "PDF Image Extractor"
    description: str = "Extracts images from a specific PDF. Input: The filename (e.g., 'knowledge.pdf')."

    def _run(self, pdf_filename: str) -> str:
        data_dir = "data"
        pdf_path = os.path.join(data_dir, pdf_filename.strip())
        output_dir = "extracted_images"
        
        if not os.path.exists(pdf_path):
            return f"Error: File '{pdf_filename}' not found."

        os.makedirs(output_dir, exist_ok=True)
        extracted_images = []
        
        try:
            doc = fitz.open(pdf_path)
            for page_index, page in enumerate(doc):
                image_list = page.get_images(full=True)
                
                for image_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Skip very small images (icons/lines)
                    if len(image_bytes) < 2000: 
                        continue

                    image_ext = base_image["ext"]
                    image_name = f"{pdf_filename}_p{page_index+1}_i{image_index+1}.{image_ext}"
                    image_save_path = os.path.join(output_dir, image_name)
                    
                    with open(image_save_path, "wb") as f:
                        f.write(image_bytes)
                    extracted_images.append(image_save_path)
            
            if not extracted_images:
                return "No significant images found in this PDF."
            
            return f"IMAGES FOUND: {', '.join(extracted_images)}"
            
        except Exception as e:
            return f"Extraction failed: {str(e)}"

# --- 4. Vision Tool ---
class VisionTool(BaseTool):
    name: str = "Vision Analyst"
    description: str = "Analyzes an image file. Input: The file path (e.g., 'extracted_images/file.png')."

    def _run(self, image_path: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not os.path.exists(image_path):
            return "Error: Image not found."

        def encode_image(path):
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        try:
            base64_image = encode_image(image_path)
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image in detail. If it is a chart or table, extract the data points. If it is a diagram, explain the process."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                "max_tokens": 400
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error analyzing image: {e}"

# Export tools
code_interpreter = CodeInterpreterTool()
file_lister = FileListerTool()
pdf_extractor = PDFImageExtractorTool()
vision_tool = VisionTool()