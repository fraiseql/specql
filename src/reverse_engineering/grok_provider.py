"""Grok LLM provider using OpenCode CLI."""

import subprocess
import json
import time
import tempfile
import uuid
from pathlib import Path
import psycopg
import os

class GrokProvider:
    """
    Grok Code Fast 1 provider via OpenCode CLI.

    Features:
    - FREE (no API costs)
    - Fast (1-3s response time)
    - Good at structured output (JSON)
    - Logs calls to PostgreSQL for metrics
    """

    def __init__(self, log_to_db: bool = True):
        """
        Initialize Grok provider.

        Args:
            log_to_db: Whether to log calls to PostgreSQL for metrics
        """
        self.model = "opencode/grok-code"
        self.log_to_db = log_to_db

        # Verify opencode is available
        try:
            result = subprocess.run(
                ["which", "opencode"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("opencode not found in PATH")
        except Exception as e:
            raise RuntimeError(f"Failed to verify opencode: {e}")

        # Database connection for logging
        if log_to_db:
            conn_string = os.getenv('SPECQL_DB_URL')
            if conn_string:
                try:
                    self.db_conn = psycopg.connect(conn_string)
                except Exception as e:
                    print(f"Warning: Could not connect to DB for logging: {e}")
                    self.db_conn = None
            else:
                self.db_conn = None
        else:
            self.db_conn = None

        print(f"✓ Grok provider ready (model: {self.model}, FREE)")

    def call(
        self,
        prompt: str,
        task_type: str = "general",
        timeout: int = 30
    ) -> str:
        """
        Call Grok via OpenCode CLI.

        Args:
            prompt: Prompt to send to Grok
            task_type: Type of task (for logging)
            timeout: Timeout in seconds

        Returns:
            Grok's response as string
        """
        call_id = str(uuid.uuid4())
        start_time = time.time()
        prompt_hash = str(hash(prompt))

        try:
            # Write prompt to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(prompt)
                prompt_file = f.name

            # Call opencode
            result = subprocess.run(
                ["opencode", "run", "--model", self.model],
                stdin=open(prompt_file),
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Clean up
            Path(prompt_file).unlink()

            if result.returncode != 0:
                raise RuntimeError(f"Grok call failed: {result.stderr}")

            response = result.stdout.strip()
            latency_ms = int((time.time() - start_time) * 1000)

            # Log call
            if self.log_to_db and self.db_conn:
                self._log_call(
                    call_id=call_id,
                    task_type=task_type,
                    prompt_length=len(prompt),
                    response_length=len(response),
                    prompt_hash=prompt_hash,
                    latency_ms=latency_ms,
                    success=True
                )

            return response

        except subprocess.TimeoutExpired:
            if self.log_to_db and self.db_conn:
                self._log_call(
                    call_id=call_id,
                    task_type=task_type,
                    prompt_length=len(prompt),
                    response_length=0,
                    prompt_hash=prompt_hash,
                    latency_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error_message=f"Timeout after {timeout}s"
                )
            raise RuntimeError(f"Grok call timed out after {timeout}s")

        except Exception as e:
            if self.log_to_db and self.db_conn:
                self._log_call(
                    call_id=call_id,
                    task_type=task_type,
                    prompt_length=len(prompt),
                    response_length=0,
                    prompt_hash=prompt_hash,
                    latency_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error_message=str(e)
                )
            raise RuntimeError(f"Grok call failed: {e}")

    def call_json(
        self,
        prompt: str,
        task_type: str = "general",
        max_retries: int = 2
    ) -> dict:
        """
        Call Grok and parse JSON response.

        Retries if JSON parsing fails.
        """
        for attempt in range(max_retries):
            response = self.call(prompt, task_type)

            try:
                # Try to parse as JSON
                return json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass

                # If last attempt, raise error
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to parse JSON from Grok response: {response[:200]}")

                # Retry with more explicit instructions
                prompt = f"{prompt}\n\nIMPORTANT: Output ONLY valid JSON, no markdown, no explanations."

        raise ValueError("Failed to get valid JSON from Grok")

    def _log_call(
        self,
        call_id: str,
        task_type: str,
        prompt_length: int,
        response_length: int,
        prompt_hash: str,
        latency_ms: int,
        success: bool,
        error_message: str = None
    ):
        """Log Grok call to PostgreSQL."""
        try:
            self.db_conn.execute(
                """
                INSERT INTO pattern_library.grok_call_logs
                (call_id, task_type, prompt_length, response_length,
                 prompt_hash, latency_ms, success, error_message, cost_usd)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0.0)
                """,
                (call_id, task_type, prompt_length, response_length,
                 prompt_hash, latency_ms, success, error_message)
            )
            self.db_conn.commit()
        except Exception:
            # Don't fail on logging errors
            pass

    def close(self):
        """Close database connection."""
        if self.db_conn:
            self.db_conn.close()