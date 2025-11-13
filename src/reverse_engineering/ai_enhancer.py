"""
AI Enhancer using local LLM (Llama 3.1 8B) or Grok

Optional cloud fallback to Anthropic API
Improves confidence from 90% → 95% through AI inference
Includes pattern discovery for novel patterns
"""

import os
import json
from typing import Optional, Dict, List, Any
from src.reverse_engineering.ast_to_specql_mapper import ConversionResult
from src.application.services.pattern_matcher import PatternMatcher
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository
)
from src.core.config import get_config


class AIEnhancer:
    """Enhance conversion with local LLM or Grok"""

    def __init__(
        self,
        local_model_path: Optional[str] = None,
        use_cloud_fallback: bool = False,
        cloud_api_key: Optional[str] = None,
        use_grok: bool = True,
        enable_pattern_discovery: bool = False
    ):
        """
        Initialize AI enhancer

        Args:
            local_model_path: Path to local LLM model
            use_cloud_fallback: Use cloud API if local fails
            cloud_api_key: Anthropic API key for fallback
            use_grok: Use Grok LLM provider instead of local/cloud
            enable_pattern_discovery: Enable automatic pattern discovery
        """
        self.local_model_path = local_model_path or os.path.expanduser("~/.specql/models/llama-3.1-8b.gguf")
        self.use_cloud_fallback = use_cloud_fallback
        self.cloud_api_key = cloud_api_key
        self.use_grok = use_grok
        self.enable_pattern_discovery = enable_pattern_discovery
        self.local_llm = None
        self.grok_provider = None

        # Initialize pattern matcher for entity enhancement (if DB available)
        config = get_config()
        self.pattern_matcher = None
        if config.database_url:
            pattern_repository = PostgreSQLPatternRepository(config.database_url)
            self.pattern_matcher = PatternMatcher(pattern_repository)

        # Try to load local model or Grok
        if self.use_grok:
            self._load_grok_provider()
        else:
            self._load_local_llm()

    def _load_local_llm(self):
        """Load local LLM model"""
        try:
            # Import llama-cpp-python conditionally
            import llama_cpp

            if os.path.exists(self.local_model_path):
                self.local_llm = llama_cpp.Llama(
                    model_path=self.local_model_path,
                    n_ctx=4096,  # Context window
                    n_gpu_layers=-1,  # Use all GPU layers if available
                    verbose=False
                )
                print(f"✅ Loaded local LLM: {self.local_model_path}")
            else:
                print(f"⚠️  Local LLM model not found: {self.local_model_path}")
                print("   Download Llama 3.1 8B from: https://huggingface.co/microsoft/WizardLM-2-8x22B")
        except ImportError:
            print("⚠️  llama-cpp-python not installed. Install with: pip install llama-cpp-python")
        except Exception as e:
            print(f"⚠️  Failed to load local LLM: {e}")

    def _load_grok_provider(self):
        """Load Grok LLM provider"""
        try:
            from src.reverse_engineering.grok_provider import GrokProvider
            self.grok_provider = GrokProvider()
            print("✅ Loaded Grok LLM provider")
        except Exception as e:
            print(f"⚠️  Failed to load Grok provider: {e}")
            self.grok_provider = None

    def enhance(self, result: ConversionResult, sql_source: str = "") -> ConversionResult:
        """
        Enhance conversion result with AI

        Args:
            result: ConversionResult from algorithmic/heuristic stages
            sql_source: Original SQL source code for pattern discovery

        Returns:
            Enhanced ConversionResult with improved confidence
        """
        # Skip if confidence already at maximum
        if result.confidence >= 0.95:
            return result

        # Skip if no LLM available
        if not self._has_llm():
            print("⚠️  No LLM available for AI enhancement")
            return result

        try:
            # Initialize metadata if not present
            if not hasattr(result, 'metadata') or result.metadata is None:
                result.metadata = {}

            # Infer function intent
            intent = self.infer_function_intent(result)
            result.metadata["intent"] = intent

            # Improve variable names
            result = self.improve_variable_names(result)

            # Suggest patterns
            suggested_patterns = self.suggest_patterns(result)
            result.metadata["suggested_patterns"] = suggested_patterns

            # Pattern discovery (if enabled)
            if self.enable_pattern_discovery and sql_source:
                discovered_patterns = self.discover_patterns(result, sql_source)
                result.metadata["discovered_patterns"] = discovered_patterns

            # Update confidence
            result.confidence = min(result.confidence + 0.05, 0.95)

        except Exception as e:
            print(f"⚠️  AI enhancement failed: {e}")
            # Don't change confidence if AI fails

        return result

    def enhance_entity(self, entity_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance entity with AI suggestions including pattern recommendations

        Now includes pattern recommendations using PatternMatcher
        """
        # ... existing enhancement logic ...

        # Suggest applicable patterns (if pattern matcher available)
        if self.pattern_matcher:
            pattern_suggestions = self.pattern_matcher.find_applicable_patterns(
                entity_spec=entity_spec,
                limit=5,
                min_confidence=0.6
            )

            # Add as metadata
            if pattern_suggestions:
                entity_spec["suggested_patterns"] = [
                    {
                        "name": pattern.name,
                        "description": pattern.description,
                        "confidence": f"{confidence:.1%}",
                        "popularity": pattern.times_instantiated
                    }
                    for pattern, confidence in pattern_suggestions
                ]

        return entity_spec

    def discover_patterns(self, result: ConversionResult, sql_source: str) -> List[Dict]:
        """
        Discover novel patterns from SQL that aren't in the pattern library

        Args:
            result: ConversionResult
            sql_source: Original SQL source code

        Returns:
            List of discovered pattern suggestions
        """
        try:
            # Check if this SQL contains novel patterns
            if not self._should_discover_patterns(result, sql_source):
                return []

            # Extract pattern from SQL using LLM
            pattern_data = self._extract_pattern_from_sql(sql_source, result)

            if pattern_data:
                # Create pattern suggestion in database
                suggestion = self._create_pattern_suggestion(pattern_data, sql_source, result)
                return [suggestion] if suggestion else []

        except Exception as e:
            print(f"⚠️  Pattern discovery failed: {e}")

        return []

    def infer_function_intent(self, result: ConversionResult) -> str:
        """
        Use LLM to infer function intent

        Args:
            result: ConversionResult

        Returns:
            Human-readable intent description
        """
        prompt = f"""You are a database expert analyzing a SQL function.

Function name: {result.function_name}
Parameters: {result.parameters}
Returns: {result.return_type}
Number of steps: {len(result.steps)}

What is the business purpose of this function? Answer in 1-2 sentences.
"""

        response = self._query_llm(prompt, max_tokens=100)
        return response.strip() if response else "Unknown purpose"

    def improve_variable_names(self, result: ConversionResult) -> ConversionResult:
        """
        Use LLM to suggest better variable names

        Args:
            result: ConversionResult

        Returns:
            Updated result with improved names
        """
        # Extract current variables
        variables = []
        for step in result.steps:
            if hasattr(step, 'variable_name') and step.variable_name:
                variables.append(step.variable_name)

        if not variables:
            return result

        prompt = f"""You are improving variable names in a database function.

Function: {result.function_name}
Current variables: {', '.join(variables)}

Suggest better names for these variables. Focus on clarity and business meaning.
Respond with JSON format: {{"old_name": "new_name", ...}}

Example: {{"v_total": "total_amount", "v_cnt": "customer_count"}}
"""

        response = self._query_llm(prompt, max_tokens=200)

        try:
            name_map = json.loads(response) if response else {}
            result = self._apply_name_map(result, name_map)
        except (json.JSONDecodeError, ValueError):
            # If LLM response not valid JSON, skip
            pass

        return result

    def suggest_patterns(self, result: ConversionResult) -> list[str]:
        """
        Suggest domain patterns that might apply

        Args:
            result: ConversionResult

        Returns:
            List of suggested pattern names
        """
        step_types = [s.type for s in result.steps]

        prompt = f"""You are analyzing a database function to detect patterns.

Function: {result.function_name}
Step types: {step_types}

Which domain patterns does this function implement? Choose from:
- state_machine (status transitions)
- audit_trail (logging changes)
- soft_delete (setting deleted flags)
- approval_workflow (multi-step approval)
- hierarchy_navigation (tree traversal)
- validation_chain (multiple validations)
- aggregation_pipeline (data aggregation)
- notification_system (sending alerts)

Respond with comma-separated pattern names, or "none".
"""

        response = self._query_llm(prompt, max_tokens=50)
        if response and response.lower() != "none":
            patterns = [p.strip() for p in response.split(",") if p.strip()]
            return patterns

        return []

    def _has_llm(self) -> bool:
        """Check if any LLM provider is available"""
        return self.local_llm is not None or self.grok_provider is not None or \
               (self.use_cloud_fallback and self.cloud_api_key is not None)

    def _query_llm(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """
        Query LLM (Grok, local, or cloud)

        Args:
            prompt: Prompt text
            max_tokens: Maximum response tokens

        Returns:
            LLM response text or None if failed
        """
        # Try Grok first (if enabled)
        if self.grok_provider:
            try:
                return self.grok_provider.call(prompt, task_type="pattern_discovery", timeout=30)
            except Exception as e:
                print(f"⚠️  Grok query failed: {e}")

        # Try local LLM
        if self.local_llm:
            try:
                response = self.local_llm(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=0.3,
                    stop=["</s>", "\n\n", "```"]
                )
                return response["choices"][0]["text"].strip()
            except Exception as e:
                print(f"⚠️  Local LLM query failed: {e}")

        # Cloud fallback
        if self.use_cloud_fallback and self.cloud_api_key:
            return self._query_cloud(prompt, max_tokens)

        return None

    def _query_cloud(self, prompt: str, max_tokens: int) -> Optional[str]:
        """Query cloud API (Anthropic)"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.cloud_api_key)

            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text.strip()
        except ImportError:
            print("⚠️  anthropic package not installed for cloud fallback")
        except Exception as e:
            print(f"⚠️  Cloud API query failed: {e}")

        return None

    def _should_discover_patterns(self, result: ConversionResult, sql_source: str) -> bool:
        """
        Determine if this SQL should trigger pattern discovery

        Criteria:
        - Low similarity to existing patterns (< 0.7)
        - High complexity (many steps, complex logic)
        - Contains novel constructs
        """
        try:
            from src.pattern_library.embeddings_pg import PatternEmbeddingService

            # Calculate complexity score
            complexity = self._calculate_complexity_score(result, sql_source)

            # Check similarity to existing patterns
            service = PatternEmbeddingService()
            query_embedding = service.embed_function(sql_source)
            similar_patterns = service.retrieve_similar(query_embedding, top_k=3, threshold=0.5)
            service.close()

            # Discovery triggers
            low_similarity = len(similar_patterns) == 0 or max(p['similarity'] for p in similar_patterns) < 0.7
            high_complexity = complexity > 0.7  # Arbitrary threshold

            return low_similarity and high_complexity

        except Exception:
            # If pattern checking fails, don't discover
            return False

    def _calculate_complexity_score(self, result: ConversionResult, sql_source: str) -> float:
        """Calculate complexity score (0-1) for pattern discovery"""
        score = 0.0

        # Number of steps
        step_count = len(result.steps)
        score += min(step_count / 20.0, 0.3)  # Max 0.3 for steps

        # SQL length
        sql_length = len(sql_source)
        score += min(sql_length / 2000.0, 0.3)  # Max 0.3 for length

        # Complex constructs
        complex_keywords = ['CASE', 'JOIN', 'UNION', 'WINDOW', 'RECURSIVE', 'CTE']
        found_complex = sum(1 for kw in complex_keywords if kw.upper() in sql_source.upper())
        score += min(found_complex / 5.0, 0.4)  # Max 0.4 for complexity

        return min(score, 1.0)

    def _extract_pattern_from_sql(self, sql_source: str, result: ConversionResult) -> Optional[Dict]:
        """
        Use LLM to extract pattern structure from SQL

        Returns:
            Pattern data dict or None if extraction fails
        """
        prompt = f"""You are a database expert analyzing SQL functions to extract reusable patterns.

Analyze this SQL function and extract a reusable business pattern:

```sql
{sql_source}
```

Function metadata:
- Name: {result.function_name}
- Parameters: {result.parameters}
- Returns: {result.return_type}
- Steps: {len(result.steps)}

Extract a pattern with these fields:
- name: A descriptive pattern name (snake_case)
- category: One of [workflow, validation, audit, hierarchy, state_machine, approval, notification, calculation, soft_delete]
- description: What this pattern does (2-3 sentences)
- parameters: JSON schema for pattern parameters
- implementation: SpecQL-style implementation structure

Respond with valid JSON only:
{{
  "name": "pattern_name",
  "category": "category_name",
  "description": "Pattern description",
  "parameters": {{"entity": {{"type": "string", "required": true}}}},
  "implementation": {{
    "fields": [...],
    "actions": [...]
  }}
}}
"""

        response = self._query_llm(prompt, max_tokens=800)
        if not response:
            return None

        try:
            pattern_data = json.loads(response)
            return pattern_data
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except (json.JSONDecodeError, ValueError):
                    pass

        return None

    def _create_pattern_suggestion(self, pattern_data: Dict, sql_source: str, result: ConversionResult) -> Optional[Dict]:
        """
        Create pattern suggestion in database

        Returns:
            Suggestion data or None if creation fails
        """
        try:
            from src.pattern_library.suggestion_service_pg import PatternSuggestionService

            service = PatternSuggestionService()

            suggestion_id = service.create_suggestion(
                suggested_name=pattern_data['name'],
                suggested_category=pattern_data['category'],
                description=pattern_data['description'],
                parameters=pattern_data.get('parameters', {}),
                implementation=pattern_data.get('implementation', {}),
                source_type='reverse_engineering',
                source_sql=sql_source,
                source_function_id=result.function_name,
                complexity_score=self._calculate_complexity_score(result, sql_source),
                confidence_score=0.8  # LLM-extracted patterns get high confidence
            )

            service.close()

            if suggestion_id:
                return {
                    'id': suggestion_id,
                    'name': pattern_data['name'],
                    'category': pattern_data['category'],
                    'description': pattern_data['description'],
                    'confidence': 0.8
                }

        except Exception as e:
            print(f"⚠️  Failed to create pattern suggestion: {e}")

        return None

    def _apply_name_map(self, result: ConversionResult, name_map: Dict[str, str]) -> ConversionResult:
        """Apply variable name mapping to result"""
        # Update variable names in steps
        for step in result.steps:
            if hasattr(step, 'variable_name') and step.variable_name in name_map:
                step.variable_name = name_map[step.variable_name]

        return result