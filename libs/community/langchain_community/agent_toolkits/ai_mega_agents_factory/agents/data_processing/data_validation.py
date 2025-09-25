"""Data Validation Agent implementation."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import re
import pandas as pd
from datetime import datetime

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


class ValidationMetrics:
    """Data validation metrics."""
    
    def __init__(self):
        """Initialize metrics."""
        self.reset()
    
    def reset(self) -> None:
        """Reset metrics."""
        self.total_records = 0
        self.valid_records = 0
        self.invalid_records = 0
        self.validation_errors = []
        self.execution_time = 0.0
        self.validation_score = 0.0


@tool
def validate_data_types(data: Dict[str, Any], schema: Dict[str, str]) -> Dict[str, Any]:
    """Validate data types against schema.
    
    Args:
        data: Data to validate
        schema: Expected data types schema
        
    Returns:
        Validation results
    """
    try:
        df = pd.DataFrame(data.get("records", []))
        validation_errors = []
        
        for column, expected_type in schema.items():
            if column not in df.columns:
                validation_errors.append(f"Missing column: {column}")
                continue
            
            column_data = df[column]
            
            if expected_type == "integer":
                invalid_count = sum(~pd.to_numeric(column_data, errors='coerce').notna())
            elif expected_type == "float":
                invalid_count = sum(~pd.to_numeric(column_data, errors='coerce').notna())
            elif expected_type == "string":
                invalid_count = sum(~column_data.astype(str).notna())
            elif expected_type == "datetime":
                invalid_count = sum(~pd.to_datetime(column_data, errors='coerce').notna())
            elif expected_type == "boolean":
                invalid_count = sum(~column_data.isin([True, False, 0, 1, "true", "false", "True", "False"]))
            else:
                invalid_count = 0
            
            if invalid_count > 0:
                validation_errors.append(f"Column {column}: {invalid_count} invalid {expected_type} values")
        
        return {
            "status": "success",
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "total_records": len(df),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def validate_constraints(data: Dict[str, Any], constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate data against business constraints.
    
    Args:
        data: Data to validate
        constraints: List of constraint rules
        
    Returns:
        Constraint validation results
    """
    try:
        df = pd.DataFrame(data.get("records", []))
        validation_errors = []
        
        for constraint in constraints:
            constraint_type = constraint.get("type")
            column = constraint.get("column")
            
            if column not in df.columns:
                validation_errors.append(f"Constraint column not found: {column}")
                continue
            
            if constraint_type == "not_null":
                null_count = df[column].isnull().sum()
                if null_count > 0:
                    validation_errors.append(f"Column {column}: {null_count} null values found")
            
            elif constraint_type == "unique":
                duplicate_count = df[column].duplicated().sum()
                if duplicate_count > 0:
                    validation_errors.append(f"Column {column}: {duplicate_count} duplicate values found")
            
            elif constraint_type == "range":
                min_val = constraint.get("min")
                max_val = constraint.get("max")
                out_of_range = 0
                
                if min_val is not None:
                    out_of_range += (df[column] < min_val).sum()
                if max_val is not None:
                    out_of_range += (df[column] > max_val).sum()
                
                if out_of_range > 0:
                    validation_errors.append(f"Column {column}: {out_of_range} values out of range [{min_val}, {max_val}]")
            
            elif constraint_type == "regex":
                pattern = constraint.get("pattern")
                if pattern:
                    regex = re.compile(pattern)
                    invalid_count = sum(~df[column].astype(str).str.match(regex, na=False))
                    if invalid_count > 0:
                        validation_errors.append(f"Column {column}: {invalid_count} values don't match pattern {pattern}")
            
            elif constraint_type == "enum":
                allowed_values = constraint.get("values", [])
                invalid_count = sum(~df[column].isin(allowed_values))
                if invalid_count > 0:
                    validation_errors.append(f"Column {column}: {invalid_count} values not in allowed set {allowed_values}")
        
        return {
            "status": "success",
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "total_records": len(df),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def validate_referential_integrity(
    data: Dict[str, Any],
    reference_data: Dict[str, Any],
    foreign_key: str,
    reference_key: str
) -> Dict[str, Any]:
    """Validate referential integrity between datasets.
    
    Args:
        data: Primary data to validate
        reference_data: Reference data
        foreign_key: Foreign key column in primary data
        reference_key: Primary key column in reference data
        
    Returns:
        Referential integrity validation results
    """
    try:
        df = pd.DataFrame(data.get("records", []))
        ref_df = pd.DataFrame(reference_data.get("records", []))
        
        if foreign_key not in df.columns:
            return {
                "status": "error",
                "error": f"Foreign key column {foreign_key} not found in data",
            }
        
        if reference_key not in ref_df.columns:
            return {
                "status": "error",
                "error": f"Reference key column {reference_key} not found in reference data",
            }
        
        # Check for orphaned records
        foreign_values = set(df[foreign_key].dropna())
        reference_values = set(ref_df[reference_key].dropna())
        
        orphaned_values = foreign_values - reference_values
        orphaned_count = df[df[foreign_key].isin(orphaned_values)].shape[0]
        
        return {
            "status": "success",
            "valid": orphaned_count == 0,
            "orphaned_records": orphaned_count,
            "orphaned_values": list(orphaned_values),
            "total_records": len(df),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def generate_data_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive data profile.
    
    Args:
        data: Data to profile
        
    Returns:
        Data profile with statistics
    """
    try:
        df = pd.DataFrame(data.get("records", []))
        
        profile = {
            "total_records": len(df),
            "total_columns": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "columns": {},
        }
        
        for column in df.columns:
            col_data = df[column]
            col_profile = {
                "data_type": str(col_data.dtype),
                "non_null_count": col_data.count(),
                "null_count": col_data.isnull().sum(),
                "null_percentage": (col_data.isnull().sum() / len(df)) * 100,
                "unique_count": col_data.nunique(),
                "duplicate_count": col_data.duplicated().sum(),
            }
            
            # Add statistics for numeric columns
            if pd.api.types.is_numeric_dtype(col_data):
                col_profile.update({
                    "min": col_data.min(),
                    "max": col_data.max(),
                    "mean": col_data.mean(),
                    "median": col_data.median(),
                    "std": col_data.std(),
                })
            
            # Add statistics for string columns
            elif pd.api.types.is_string_dtype(col_data):
                col_profile.update({
                    "min_length": col_data.str.len().min(),
                    "max_length": col_data.str.len().max(),
                    "avg_length": col_data.str.len().mean(),
                })
            
            profile["columns"][column] = col_profile
        
        return {
            "status": "success",
            "profile": profile,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


class DataValidationAgent(BaseMegaAgent):
    """Data Validation Agent for comprehensive data quality validation."""
    
    def __init__(
        self,
        config: Optional[MegaAgentConfig] = None,
        llm: Optional[BaseLanguageModel] = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ):
        """Initialize Data Validation Agent.
        
        Args:
            config: Agent configuration
            llm: Language model
            callback_manager: Callback manager
            **kwargs: Additional arguments
        """
        if config is None:
            manifest = MegaAgentManifest(
                name="Data Validation Agent",
                version="1.0.0",
                category=AgentCategory.DATA_PROCESSING,
                description="Enterprise data validation agent for quality assurance",
                author="AI Mega Agents Factory",
                tags=["validation", "quality", "data", "constraints"],
                min_langchain_version="0.1.0",
                supported_llm_types=["openai", "anthropic", "huggingface"],
                required_tools=["pandas", "regex"],
                monetization_tier=MonetizationTier.BASIC,
                pricing_model="usage_based",
            )
            config = MegaAgentConfig(manifest=manifest)
        
        super().__init__(config, llm, callback_manager, **kwargs)
        self.metrics = ValidationMetrics()
        
    def initialize(self) -> None:
        """Initialize the validation agent."""
        if self._initialized:
            return
            
        self._tools = self.get_tools()
        self._initialized = True
    
    def get_tools(self) -> List[BaseTool]:
        """Get validation tools.
        
        Returns:
            List of validation tools
        """
        return [
            validate_data_types,
            validate_constraints,
            validate_referential_integrity,
            generate_data_profile,
        ]
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute data validation.
        
        Args:
            input_data: Input data with validation rules
            **kwargs: Additional execution parameters
            
        Returns:
            Validation results
        """
        start_time = time.time()
        self.metrics.reset()
        
        try:
            if not self.validate_input(input_data):
                return {
                    "status": "error",
                    "error": "Invalid input data",
                    "required_fields": ["data", "validation_rules"],
                }
            
            data = input_data.get("data", {})
            validation_rules = input_data.get("validation_rules", {})
            
            self.metrics.total_records = len(data.get("records", []))
            validation_results = []
            
            # Data type validation
            if "schema" in validation_rules:
                type_result = await self._validate_types(data, validation_rules["schema"])
                validation_results.append(type_result)
            
            # Constraint validation
            if "constraints" in validation_rules:
                constraint_result = await self._validate_constraints(data, validation_rules["constraints"])
                validation_results.append(constraint_result)
            
            # Referential integrity validation
            if "referential_integrity" in validation_rules:
                ref_result = await self._validate_referential_integrity(
                    data, validation_rules["referential_integrity"]
                )
                validation_results.append(ref_result)
            
            # Generate data profile if requested
            profile_result = None
            if input_data.get("generate_profile", False):
                profile_result = await self._generate_profile(data)
            
            # Calculate overall validation score
            total_errors = sum(len(result.get("errors", [])) for result in validation_results if result.get("status") == "success")
            self.metrics.validation_score = max(0, 1 - (total_errors / max(self.metrics.total_records, 1)))
            
            self.metrics.execution_time = time.time() - start_time
            
            return {
                "status": "success",
                "validation_score": self.metrics.validation_score,
                "total_records": self.metrics.total_records,
                "execution_time": self.metrics.execution_time,
                "validation_results": validation_results,
                "data_profile": profile_result,
                "summary": {
                    "is_valid": all(result.get("valid", False) for result in validation_results if result.get("status") == "success"),
                    "total_errors": total_errors,
                },
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time,
            }
    
    async def _validate_types(self, data: Dict[str, Any], schema: Dict[str, str]) -> Dict[str, Any]:
        """Validate data types."""
        return validate_data_types.invoke({"data": data, "schema": schema})
    
    async def _validate_constraints(self, data: Dict[str, Any], constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate constraints."""
        return validate_constraints.invoke({"data": data, "constraints": constraints})
    
    async def _validate_referential_integrity(self, data: Dict[str, Any], ref_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate referential integrity."""
        return validate_referential_integrity.invoke({
            "data": data,
            "reference_data": ref_config.get("reference_data"),
            "foreign_key": ref_config.get("foreign_key"),
            "reference_key": ref_config.get("reference_key"),
        })
    
    async def _generate_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data profile."""
        return generate_data_profile.invoke({"data": data})
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["data", "validation_rules"]
        
        for field in required_fields:
            if field not in input_data:
                return False
        
        data = input_data["data"]
        if not isinstance(data, dict) or "records" not in data:
            return False
        
        validation_rules = input_data["validation_rules"]
        if not isinstance(validation_rules, dict):
            return False
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get validation metrics.
        
        Returns:
            Current metrics
        """
        return {
            "total_records": self.metrics.total_records,
            "valid_records": self.metrics.valid_records,
            "invalid_records": self.metrics.invalid_records,
            "validation_score": self.metrics.validation_score,
            "execution_time": self.metrics.execution_time,
            "validation_errors": len(self.metrics.validation_errors),
        }