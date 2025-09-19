"""
Document Processing Agent - AI Mega Agents Factory

Specialized agent for document processing, text extraction, and format conversion.
Supports PDF, Word, Excel, and other common document formats.
"""

import base64
from typing import Any, Dict, List, Optional
import asyncio
import time
import re
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

from ai_mega_agents_factory import (
    BaseAgentFactory, AgentConfig, AgentResult, AgentTier, monetization_service
)


class DocumentConfig(AgentConfig):
    """Configuration for Document Processing Agent"""
    max_file_size_mb: int = 10
    supported_formats: List[str] = ["pdf", "docx", "xlsx", "txt", "csv"]
    ocr_enabled: bool = True
    
    class Config:
        extra = "allow"


class TextExtractionTool(BaseTool):
    """Tool for extracting text from documents"""
    name = "text_extractor"
    description = "Extract text content from various document formats"
    
    def _run(self, file_data: str, file_type: str = "txt") -> str:
        """Extract text from document"""
        try:
            # For demo purposes, simulate text extraction
            # In production, use libraries like PyPDF2, python-docx, etc.
            
            if file_type.lower() == "pdf":
                return f"Extracted text from PDF document: Sample PDF content with {len(file_data)} characters"
            
            elif file_type.lower() == "docx":
                return f"Extracted text from Word document: Sample Word content with {len(file_data)} characters"
            
            elif file_type.lower() == "xlsx":
                return f"Extracted data from Excel spreadsheet: Sample Excel data with {len(file_data)} characters"
            
            elif file_type.lower() == "txt":
                return f"Plain text content: {file_data[:1000]}..."  # First 1000 chars
            
            else:
                return f"Unsupported file type: {file_type}"
                
        except Exception as e:
            return f"Text extraction failed: {str(e)}"
    
    async def _arun(self, file_data: str, file_type: str = "txt") -> str:
        """Async version of text extraction"""
        return self._run(file_data, file_type)


class DocumentConverterTool(BaseTool):
    """Tool for converting between document formats"""
    name = "document_converter"
    description = "Convert documents between different formats"
    
    def _run(self, content: str, source_format: str, target_format: str) -> str:
        """Convert document format"""
        try:
            # Mock conversion logic
            conversion_map = {
                ("txt", "html"): lambda x: f"<html><body><p>{x}</p></body></html>",
                ("txt", "markdown"): lambda x: f"# Document\n\n{x}",
                ("html", "txt"): lambda x: re.sub(r'<[^>]+>', '', x),
                ("markdown", "html"): lambda x: f"<html><body>{x.replace('#', '<h1>').replace('\n', '<br>')}</body></html>"
            }
            
            if (source_format, target_format) in conversion_map:
                converted = conversion_map[(source_format, target_format)](content)
                return f"Successfully converted from {source_format} to {target_format}: {converted[:500]}..."
            else:
                return f"Conversion from {source_format} to {target_format} not supported"
                
        except Exception as e:
            return f"Document conversion failed: {str(e)}"
    
    async def _arun(self, content: str, source_format: str, target_format: str) -> str:
        """Async version of document conversion"""
        return self._run(content, source_format, target_format)


class DocumentAnalysisTool(BaseTool):
    """Tool for analyzing document content"""
    name = "document_analyzer"
    description = "Analyze document structure, metadata, and content"
    
    def _run(self, content: str) -> str:
        """Analyze document content"""
        try:
            # Basic content analysis
            analysis = {
                "character_count": len(content),
                "word_count": len(content.split()),
                "paragraph_count": len(content.split('\n\n')),
                "line_count": len(content.split('\n')),
                "average_words_per_sentence": len(content.split()) / max(len(re.split(r'[.!?]+', content)), 1),
                "readability_score": min(100, max(0, 206.835 - 1.015 * (len(content.split()) / max(len(re.split(r'[.!?]+', content)), 1)) - 84.6 * (len([c for c in content if c.lower() in 'aeiou']) / max(len(content.split()), 1)))),
                "contains_tables": "table" in content.lower() or "|" in content,
                "contains_images": "image" in content.lower() or "fig" in content.lower(),
                "language": "en",  # Mock language detection
                "sentiment": "neutral"  # Mock sentiment
            }
            
            return str(analysis)
            
        except Exception as e:
            return f"Document analysis failed: {str(e)}"
    
    async def _arun(self, content: str) -> str:
        """Async version of document analysis"""
        return self._run(content)


class OCRTool(BaseTool):
    """Tool for optical character recognition"""
    name = "ocr_processor"
    description = "Extract text from images and scanned documents"
    
    def _run(self, image_data: str) -> str:
        """Perform OCR on image data"""
        try:
            # Mock OCR processing
            # In production, use libraries like Tesseract, Cloud Vision API, etc.
            return f"OCR extracted text from image: Sample extracted text with {len(image_data)} data bytes processed"
            
        except Exception as e:
            return f"OCR processing failed: {str(e)}"
    
    async def _arun(self, image_data: str) -> str:
        """Async version of OCR"""
        return self._run(image_data)


class DocumentProcessingAgent(BaseAgentFactory):
    """Advanced Document Processing Agent"""
    
    def __init__(self, config: DocumentConfig):
        super().__init__(config)
        self.config = config
        self._extractor_tool = TextExtractionTool()
        self._converter_tool = DocumentConverterTool()
        self._analyzer_tool = DocumentAnalysisTool()
        self._ocr_tool = OCRTool()
    
    async def initialize(self) -> bool:
        """Initialize the document processing agent"""
        try:
            # Initialize tools
            self._tools = [
                self._extractor_tool, 
                self._converter_tool, 
                self._analyzer_tool,
                self._ocr_tool
            ]
            return True
        except Exception as e:
            return False
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """Execute document processing task"""
        start_time = time.time()
        
        try:
            action = task.get("action", "extract")
            
            # Check tier limits
            file_size = len(str(task.get("data", ""))) / (1024 * 1024)  # MB
            if self.config.tier == AgentTier.FREE and file_size > 2:
                return AgentResult(
                    success=False,
                    error="File size exceeds free tier limit (2MB). Upgrade for larger files.",
                    execution_time=time.time() - start_time
                )
            
            if action == "extract":
                result = await self._extractor_tool._arun(
                    file_data=task.get("data", ""),
                    file_type=task.get("file_type", "txt")
                )
                operation = "text_extraction"
                
            elif action == "convert":
                result = await self._converter_tool._arun(
                    content=task.get("content", ""),
                    source_format=task.get("source_format", "txt"),
                    target_format=task.get("target_format", "html")
                )
                operation = "document_conversion"
                
            elif action == "analyze":
                result = await self._analyzer_tool._arun(
                    content=task.get("content", "")
                )
                operation = "document_analysis"
                
            elif action == "ocr":
                if not self.config.ocr_enabled:
                    return AgentResult(
                        success=False,
                        error="OCR is not enabled in configuration",
                        execution_time=time.time() - start_time
                    )
                
                result = await self._ocr_tool._arun(
                    image_data=task.get("image_data", "")
                )
                operation = "ocr_processing"
                
            else:
                return AgentResult(
                    success=False,
                    error=f"Unknown action: {action}",
                    execution_time=time.time() - start_time
                )
            
            # Track usage
            monetization_service.track_usage(self.config.agent_id, operation)
            
            return AgentResult(
                success=True,
                data={
                    "action": action,
                    "result": result,
                    "agent_version": self.config.version
                },
                metadata={
                    "tier": self.config.tier.value,
                    "operation": operation,
                    "file_size_mb": file_size
                },
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def cleanup(self) -> bool:
        """Cleanup resources"""
        try:
            # Clean up temporary files, connections, etc.
            return True
        except Exception:
            return False
    
    def get_tools(self) -> List[BaseTool]:
        """Get agent tools"""
        return self._tools


# Register the agent
from ai_mega_agents_factory import agent_registry
agent_registry.register_agent_type("document_processing", DocumentProcessingAgent)