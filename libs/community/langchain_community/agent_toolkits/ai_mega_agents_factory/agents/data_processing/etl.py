"""ETL (Extract, Transform, Load) Agent implementation."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import pandas as pd
from langchain_core.callbacks import BaseCallbackManager
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool, tool

from langchain_community.agent_toolkits.ai_mega_agents_factory.base import (
    AgentCategory,
    BaseMegaAgent,
    MegaAgentConfig,
    MegaAgentManifest,
    MonetizationTier,
)


class ETLMetrics:
    """ETL operation metrics."""
    
    def __init__(self):
        """Initialize metrics."""
        self.reset()
    
    def reset(self) -> None:
        """Reset metrics."""
        self.records_extracted = 0
        self.records_transformed = 0
        self.records_loaded = 0
        self.errors_count = 0
        self.execution_time = 0.0
        self.data_quality_score = 0.0
        self.throughput_per_second = 0.0


@tool
def extract_from_csv(file_path: str, delimiter: str = ",") -> Dict[str, Any]:
    """Extract data from CSV file.
    
    Args:
        file_path: Path to CSV file
        delimiter: CSV delimiter
        
    Returns:
        Extracted data information
    """
    try:
        df = pd.read_csv(file_path, delimiter=delimiter)
        return {
            "status": "success",
            "records_count": len(df),
            "columns": list(df.columns),
            "data_types": df.dtypes.to_dict(),
            "sample": df.head().to_dict(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def extract_from_json(file_path: str) -> Dict[str, Any]:
    """Extract data from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Extracted data information
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return {
                "status": "success",
                "records_count": len(data),
                "structure": "array",
                "sample": data[:5] if data else [],
            }
        else:
            return {
                "status": "success",
                "records_count": 1,
                "structure": "object",
                "keys": list(data.keys()) if isinstance(data, dict) else [],
                "sample": data,
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def transform_data(data: Dict[str, Any], transformations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply transformations to data.
    
    Args:
        data: Data to transform
        transformations: List of transformation operations
        
    Returns:
        Transformation results
    """
    try:
        # Create DataFrame from data
        if "sample" in data and isinstance(data["sample"], dict):
            df = pd.DataFrame([data["sample"]])
        else:
            df = pd.DataFrame(data.get("records", []))
        
        transformed_count = 0
        
        for transform in transformations:
            operation = transform.get("operation")
            
            if operation == "rename_column":
                old_name = transform.get("old_name")
                new_name = transform.get("new_name")
                if old_name in df.columns:
                    df = df.rename(columns={old_name: new_name})
                    transformed_count += 1
            
            elif operation == "filter_rows":
                condition = transform.get("condition")
                column = transform.get("column")
                value = transform.get("value")
                
                if column in df.columns:
                    if condition == "equals":
                        df = df[df[column] == value]
                    elif condition == "greater_than":
                        df = df[df[column] > value]
                    elif condition == "less_than":
                        df = df[df[column] < value]
                    transformed_count += 1
            
            elif operation == "add_column":
                column_name = transform.get("column_name")
                column_value = transform.get("column_value")
                df[column_name] = column_value
                transformed_count += 1
            
            elif operation == "convert_type":
                column = transform.get("column")
                target_type = transform.get("target_type")
                
                if column in df.columns:
                    if target_type == "string":
                        df[column] = df[column].astype(str)
                    elif target_type == "numeric":
                        df[column] = pd.to_numeric(df[column], errors='coerce')
                    elif target_type == "datetime":
                        df[column] = pd.to_datetime(df[column], errors='coerce')
                    transformed_count += 1
        
        return {
            "status": "success",
            "records_count": len(df),
            "transformations_applied": transformed_count,
            "columns": list(df.columns),
            "sample": df.head().to_dict(),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def load_to_csv(data: Dict[str, Any], output_path: str) -> Dict[str, Any]:
    """Load data to CSV file.
    
    Args:
        data: Data to load
        output_path: Output CSV file path
        
    Returns:
        Load operation results
    """
    try:
        # Convert data to DataFrame
        if "sample" in data and isinstance(data["sample"], dict):
            df = pd.DataFrame([data["sample"]])
        else:
            df = pd.DataFrame(data.get("records", []))
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        return {
            "status": "success",
            "records_loaded": len(df),
            "output_path": output_path,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def validate_data_quality(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate data quality.
    
    Args:
        data: Data to validate
        
    Returns:
        Data quality metrics
    """
    try:
        if "sample" in data and isinstance(data["sample"], dict):
            df = pd.DataFrame([data["sample"]])
        else:
            df = pd.DataFrame(data.get("records", []))
        
        total_cells = df.size
        null_cells = df.isnull().sum().sum()
        duplicate_rows = df.duplicated().sum()
        
        quality_score = 1.0 - (null_cells / total_cells if total_cells > 0 else 0)
        
        return {
            "status": "success",
            "total_records": len(df),
            "total_cells": total_cells,
            "null_cells": int(null_cells),
            "duplicate_rows": int(duplicate_rows),
            "quality_score": round(quality_score, 3),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


class ETLAgent(BaseMegaAgent):
    """ETL (Extract, Transform, Load) Agent for data processing pipelines."""
    
    def __init__(
        self,
        config: Optional[MegaAgentConfig] = None,
        llm: Optional[BaseLanguageModel] = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ):
        """Initialize ETL Agent.
        
        Args:
            config: Agent configuration
            llm: Language model
            callback_manager: Callback manager
            **kwargs: Additional arguments
        """
        if config is None:
            manifest = MegaAgentManifest(
                name="ETL Agent",
                version="1.0.0",
                category=AgentCategory.DATA_PROCESSING,
                description="Enterprise ETL agent for data extraction, transformation, and loading",
                author="AI Mega Agents Factory",
                tags=["etl", "data", "processing", "pipeline"],
                min_langchain_version="0.1.0",
                supported_llm_types=["openai", "anthropic", "huggingface"],
                required_tools=["csv", "json", "pandas"],
                monetization_tier=MonetizationTier.BASIC,
                pricing_model="usage_based",
            )
            config = MegaAgentConfig(manifest=manifest)
        
        super().__init__(config, llm, callback_manager, **kwargs)
        self.metrics = ETLMetrics()
        
    def initialize(self) -> None:
        """Initialize the ETL agent."""
        if self._initialized:
            return
            
        # Initialize tools
        self._tools = self.get_tools()
        self._initialized = True
    
    def get_tools(self) -> List[BaseTool]:
        """Get ETL tools.
        
        Returns:
            List of ETL tools
        """
        return [
            extract_from_csv,
            extract_from_json,
            transform_data,
            load_to_csv,
            validate_data_quality,
        ]
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute ETL pipeline.
        
        Args:
            input_data: Input configuration with source, transformations, and target
            **kwargs: Additional execution parameters
            
        Returns:
            ETL execution results
        """
        start_time = time.time()
        self.metrics.reset()
        
        try:
            # Validate input
            if not self.validate_input(input_data):
                return {
                    "status": "error",
                    "error": "Invalid input data",
                    "required_fields": ["source", "target"],
                }
            
            source_config = input_data.get("source", {})
            transform_config = input_data.get("transformations", [])
            target_config = input_data.get("target", {})
            
            # Extract phase
            extract_result = await self._extract_data(source_config)
            if extract_result.get("status") != "success":
                return extract_result
            
            self.metrics.records_extracted = extract_result.get("records_count", 0)
            
            # Transform phase
            if transform_config:
                transform_result = await self._transform_data(extract_result, transform_config)
                if transform_result.get("status") != "success":
                    return transform_result
                extract_result = transform_result
            
            self.metrics.records_transformed = extract_result.get("records_count", 0)
            
            # Load phase
            load_result = await self._load_data(extract_result, target_config)
            if load_result.get("status") != "success":
                return load_result
            
            self.metrics.records_loaded = load_result.get("records_loaded", 0)
            
            # Calculate metrics
            self.metrics.execution_time = time.time() - start_time
            if self.metrics.execution_time > 0:
                self.metrics.throughput_per_second = self.metrics.records_loaded / self.metrics.execution_time
            
            # Validate data quality
            quality_result = await self._validate_quality(extract_result)
            self.metrics.data_quality_score = quality_result.get("quality_score", 0.0)
            
            return {
                "status": "success",
                "execution_time": self.metrics.execution_time,
                "records_processed": {
                    "extracted": self.metrics.records_extracted,
                    "transformed": self.metrics.records_transformed,
                    "loaded": self.metrics.records_loaded,
                },
                "data_quality_score": self.metrics.data_quality_score,
                "throughput_per_second": self.metrics.throughput_per_second,
                "output": load_result,
            }
            
        except Exception as e:
            self.metrics.errors_count += 1
            return {
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time,
            }
    
    async def _extract_data(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from source.
        
        Args:
            source_config: Source configuration
            
        Returns:
            Extraction results
        """
        source_type = source_config.get("type")
        source_path = source_config.get("path")
        
        if source_type == "csv":
            delimiter = source_config.get("delimiter", ",")
            return extract_from_csv.invoke({"file_path": source_path, "delimiter": delimiter})
        elif source_type == "json":
            return extract_from_json.invoke({"file_path": source_path})
        else:
            return {
                "status": "error",
                "error": f"Unsupported source type: {source_type}",
            }
    
    async def _transform_data(
        self,
        data: Dict[str, Any],
        transformations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Transform extracted data.
        
        Args:
            data: Extracted data
            transformations: List of transformations
            
        Returns:
            Transformation results
        """
        return transform_data.invoke({"data": data, "transformations": transformations})
    
    async def _load_data(
        self,
        data: Dict[str, Any],
        target_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Load data to target.
        
        Args:
            data: Data to load
            target_config: Target configuration
            
        Returns:
            Load results
        """
        target_type = target_config.get("type")
        target_path = target_config.get("path")
        
        if target_type == "csv":
            return load_to_csv.invoke({"data": data, "output_path": target_path})
        else:
            return {
                "status": "error",
                "error": f"Unsupported target type: {target_type}",
            }
    
    async def _validate_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data quality.
        
        Args:
            data: Data to validate
            
        Returns:
            Quality validation results
        """
        return validate_data_quality.invoke({"data": data})
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate ETL input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["source", "target"]
        
        for field in required_fields:
            if field not in input_data:
                return False
        
        source = input_data["source"]
        if not isinstance(source, dict) or "type" not in source or "path" not in source:
            return False
        
        target = input_data["target"]
        if not isinstance(target, dict) or "type" not in target or "path" not in target:
            return False
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get ETL agent metrics.
        
        Returns:
            Current metrics
        """
        return {
            "records_extracted": self.metrics.records_extracted,
            "records_transformed": self.metrics.records_transformed,
            "records_loaded": self.metrics.records_loaded,
            "errors_count": self.metrics.errors_count,
            "execution_time": self.metrics.execution_time,
            "data_quality_score": self.metrics.data_quality_score,
            "throughput_per_second": self.metrics.throughput_per_second,
        }