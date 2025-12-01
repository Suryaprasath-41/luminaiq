from pypdf import PdfReader
from docx import Document as DocxDocument
from io import BytesIO
from typing import List, Dict, Tuple
import re


class DocumentService:
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        pdf_reader = PdfReader(BytesIO(file_content))
        text = ""
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        return self._clean_text(text)

    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        doc = DocxDocument(BytesIO(file_content))
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return self._clean_text(text)

    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text based on file type"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            return self.extract_text_from_pdf(file_content)
        elif filename_lower.endswith('.docx'):
            return self.extract_text_from_docx(file_content)
        elif filename_lower.endswith('.txt'):
            return self._clean_text(file_content.decode('utf-8'))
        else:
            raise ValueError(f"Unsupported file type: {filename}")

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might cause issues
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()

    def detect_chapters(self, text: str) -> List[Dict[str, str]]:
        """
        Detect chapters in text and split accordingly.
        Returns list of dicts with chapter_number, title, and content.
        """
        # Common chapter patterns
        chapter_patterns = [
            r'(?:^|\n)(?:Chapter|CHAPTER)\s+(\d+)[:\.\s]*([^\n]*)',
            r'(?:^|\n)(?:Unit|UNIT)\s+(\d+)[:\.\s]*([^\n]*)',
            r'(?:^|\n)(\d+)\.\s+([A-Z][^\n]*)',
            r'(?:^|\n)(?:Module|MODULE)\s+(\d+)[:\.\s]*([^\n]*)',
        ]
        
        chapters = []
        found_chapters = []
        
        for pattern in chapter_patterns:
            matches = list(re.finditer(pattern, text))
            if matches:
                found_chapters = matches
                break
        
        if not found_chapters:
            # No chapters detected, treat entire text as one chapter
            return [{
                "chapter_number": 1,
                "title": "Main Content",
                "content": text
            }]
        
        for i, match in enumerate(found_chapters):
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip() if match.group(2) else f"Chapter {chapter_num}"
            
            start_pos = match.end()
            
            if i + 1 < len(found_chapters):
                end_pos = found_chapters[i + 1].start()
            else:
                end_pos = len(text)
            
            content = text[start_pos:end_pos].strip()
            
            chapters.append({
                "chapter_number": chapter_num,
                "title": chapter_title,
                "content": content
            })
        
        return chapters

    def split_into_sections(
        self,
        text: str,
        section_size: int = 2000
    ) -> List[Tuple[str, str]]:
        """
        Split text into sections of approximate size.
        Returns list of tuples (section_title, content).
        """
        words = text.split()
        sections = []
        current_section = []
        current_size = 0
        section_num = 1
        
        for word in words:
            current_section.append(word)
            current_size += len(word) + 1
            
            if current_size >= section_size:
                sections.append((
                    f"Section {section_num}",
                    " ".join(current_section)
                ))
                current_section = []
                current_size = 0
                section_num += 1
        
        if current_section:
            sections.append((
                f"Section {section_num}",
                " ".join(current_section)
            ))
        
        return sections
