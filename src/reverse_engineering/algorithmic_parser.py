"""
Algorithmic Parser: SQL → SpecQL without AI

85% confidence through pure algorithmic conversion
"""

from src.reverse_engineering.sql_ast_parser import SQLASTParser
from src.reverse_engineering.ast_to_specql_mapper import ASTToSpecQLMapper, ConversionResult
from src.reverse_engineering.heuristic_enhancer import HeuristicEnhancer
from src.reverse_engineering.ai_enhancer import AIEnhancer
from typing import Dict
import yaml


class AlgorithmicParser:
    """
    Algorithmic SQL → SpecQL parser with optional enhancements

    Three-stage pipeline:
    1. Algorithmic parsing (85% confidence)
    2. Heuristic enhancement (90% confidence)
    3. AI enhancement (95% confidence)
    """

    def __init__(self, use_heuristics: bool = True, use_ai: bool = False, enable_pattern_discovery: bool = False):
        self.sql_parser = SQLASTParser()
        self.mapper = ASTToSpecQLMapper()
        self.heuristic_enhancer = HeuristicEnhancer() if use_heuristics else None
        self.ai_enhancer = AIEnhancer(enable_pattern_discovery=enable_pattern_discovery) if use_ai else None

    def parse(self, sql: str) -> ConversionResult:
        """
        Parse SQL function to SpecQL

        Args:
            sql: SQL CREATE FUNCTION statement

        Returns:
            ConversionResult with SpecQL steps and confidence
        """
        # Stage 1: Parse SQL to AST
        parsed_func = self.sql_parser.parse_function(sql)

        # Stage 2: Map AST to SpecQL primitives
        result = self.mapper.map_function(parsed_func)

        # Stage 3: Apply heuristic enhancements (optional)
        if self.heuristic_enhancer:
            result = self.heuristic_enhancer.enhance(result)

        # Stage 4: Apply AI enhancements (optional)
        if self.ai_enhancer:
            result = self.ai_enhancer.enhance(result, sql)

        return result

    def parse_to_yaml(self, sql: str) -> str:
        """
        Parse SQL and convert to YAML

        Args:
            sql: SQL CREATE FUNCTION statement

        Returns:
            SpecQL YAML string
        """
        result = self.parse(sql)
        return self._to_yaml(result)

    def _to_yaml(self, result: ConversionResult) -> str:
        """Convert ConversionResult to YAML string"""
        yaml_dict = {
            "entity": result.function_name.replace("_", " ").title().replace(" ", ""),
            "schema": result.schema,
            "actions": [
                {
                    "name": result.function_name,
                    "parameters": result.parameters,
                    "returns": result.return_type,
                    "steps": [self._step_to_dict(s) for s in result.steps]
                }
            ],
            "_metadata": {
                "confidence": result.confidence,
                "warnings": result.warnings,
                "generated_by": "algorithmic_parser"
            }
        }

        return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)

    def _step_to_dict(self, step) -> Dict:
        """Convert ActionStep to dict for YAML"""
        step_dict = {"type": step.type}

        if step.type == "declare":
            step_dict = {
                "declare": {
                    "name": step.variable_name,
                    "type": step.variable_type,
                    "default": step.default_value
                }
            }

        elif step.type == "assign":
            step_dict = {
                "assign": f"{step.variable_name} = {step.expression}"
            }

        elif step.type == "query":
            step_dict = {
                "query": step.sql
            }
            if step.store_result:
                step_dict["into"] = step.store_result

        elif step.type == "cte":
            step_dict = {
                "cte": {
                    "name": step.cte_name,
                    "query": step.cte_query
                }
            }

        elif step.type == "if":
            step_dict = {
                "if": step.condition,
                "then": [self._step_to_dict(s) for s in step.then_steps]
            }
            if step.else_steps:
                step_dict["else"] = [self._step_to_dict(s) for s in step.else_steps]

        elif step.type == "return":
            step_dict = {
                "return": step.return_value
            }

        elif step.type == "return_table":
            step_dict = {
                "return_table": step.return_table_query
            }

        elif step.type == "for_query":
            step_dict = {
                "for_query": {
                    "alias": step.for_query_alias,
                    "query": step.for_query_sql,
                    "body": [self._step_to_dict(s) for s in step.for_query_body]
                }
            }

        elif step.type == "while":
            step_dict = {
                "while": {
                    "condition": step.while_condition,
                    "body": [self._step_to_dict(s) for s in step.loop_body]
                }
            }

        return step_dict