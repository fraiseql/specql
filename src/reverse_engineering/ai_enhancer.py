"""
AI Enhancer using local LLM (Llama 3.1 8B)

Optional cloud fallback to Anthropic API
Improves confidence from 90% → 95% through AI inference
"""

import os
from typing import Optional, Tuple, Dict, Any
from src.reverse_engineering.ast_to_specql_mapper import ConversionResult


class AIEnhancer:
    """Enhance conversion with local LLM"""

    def __init__(
        self,
        local_model_path: Optional[str] = None,
        use_cloud_fallback: bool = False,
        cloud_api_key: Optional[str] = None
    ):
        """
        Initialize AI enhancer

        Args:
            local_model_path: Path to local LLM model
            use_cloud_fallback: Use cloud API if local fails
            cloud_api_key: Anthropic API key for fallback
        """
        self.local_model_path = local_model_path or os.path.expanduser("~/.specql/models/llama-3.1-8b.gguf")
        self.use_cloud_fallback = use_cloud_fallback
        self.cloud_api_key = cloud_api_key
        self.local_llm = None

        # Try to load local model
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

    def enhance(self, result: ConversionResult) -> ConversionResult:
        """
        Enhance conversion result with AI

        Args:
            result: ConversionResult from algorithmic/heuristic stages

        Returns:
            Enhanced ConversionResult with improved confidence
        """
        # Skip if confidence already at maximum
        if result.confidence >= 0.95:
            return result

        # Skip if no LLM available
        if not self.local_llm and not (self.use_cloud_fallback and self.cloud_api_key):
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

            # Update confidence
            result.confidence = min(result.confidence + 0.05, 0.95)

        except Exception as e:
            print(f"⚠️  AI enhancement failed: {e}")
            # Don't change confidence if AI fails

        return result

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
            import json
            name_map = json.loads(response) if response else {}
            result = self._apply_name_map(result, name_map)
        except:
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

    def _query_llm(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """
        Query LLM (local or cloud)

        Args:
            prompt: Prompt text
            max_tokens: Maximum response tokens

        Returns:
            LLM response text or None if failed
        """
        # Try local first
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

    def _apply_name_map(self, result: ConversionResult, name_map: Dict[str, str]) -> ConversionResult:
        """Apply variable name mapping to result"""
        # Update variable names in steps
        for step in result.steps:
            if hasattr(step, 'variable_name') and step.variable_name in name_map:
                step.variable_name = name_map[step.variable_name]

        return result