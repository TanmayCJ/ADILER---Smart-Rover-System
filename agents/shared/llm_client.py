"""
Llama 3.1 LLM client for agent reasoning.
Supports Ollama local instances and remote endpoints via LiteLLM.
"""

import logging
import os
from typing import Optional, Dict, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class LlamaClient:
    """
    Client for invoking Llama 3.1 for agent reasoning.
    Falls back gracefully if LLM is unavailable (returns mock responses).
    """
    
    def __init__(
        self,
        model: str = "llama2",  # "llama2", "llama3.1", or custom
        base_url: str = "http://localhost:11434",
        api_key: Optional[str] = None,
        use_local: bool = True,
        fallback_mode: bool = False
    ):
        """
        Initialize Llama client.
        
        Args:
            model: Model name (default: llama2, change to llama3.1 if available)
            base_url: Ollama endpoint (default: local)
            api_key: API key for remote endpoints (optional)
            use_local: Use local Ollama (True) or remote LiteLLM (False)
            fallback_mode: If True, return mock responses instead of calling LLM
        """
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.use_local = use_local
        self.fallback_mode = fallback_mode
        self.invocation_count = 0
        
        # Try to import Ollama client
        self.client = None
        if use_local:
            try:
                import ollama
                self.client = ollama.Client(host=base_url)
                logger.info(f"✓ Connected to local Ollama at {base_url}")
            except ImportError:
                logger.warning("ollama package not found. Install with: pip install ollama")
                self.fallback_mode = True
            except Exception as e:
                logger.warning(f"Failed to connect to Ollama: {e}. Using fallback mode.")
                self.fallback_mode = True
        else:
            try:
                import litellm
                self.litellm = litellm
                logger.info(f"✓ LiteLLM client initialized")
            except ImportError:
                logger.warning("litellm package not found. Install with: pip install litellm")
                self.fallback_mode = True
    
    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 30
    ) -> str:
        """
        Invoke Llama model for reasoning.
        
        Args:
            prompt: User prompt/query
            system_prompt: System-level instructions (optional)
            temperature: Sampling temperature (0-1)
            max_tokens: Max response tokens
            timeout: Request timeout in seconds
            
        Returns:
            LLM response string
        """
        self.invocation_count += 1
        
        # Log invocation
        logger.debug(f"[LLM Call #{self.invocation_count}] Model: {self.model}, Prompt len: {len(prompt)}")
        
        if os.environ.get("THRESHOLD_ONLY", "0") == "1":
            return self._get_fallback_response(prompt, system_prompt)

        if self.fallback_mode:
            logger.debug("Using fallback (mock) response mode")
            return self._get_fallback_response(prompt, system_prompt)
        
        if self.use_local:
            return self._invoke_ollama(prompt, system_prompt, temperature, max_tokens)
        else:
            return self._invoke_litellm(prompt, system_prompt, temperature, max_tokens)
    
    def _invoke_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Invoke local Ollama instance."""
        try:
            # Build full prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            # Call Ollama
            options = {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
            if os.environ.get("OLLAMA_FORCE_CPU", "").lower() in {"1", "true", "yes"}:
                options["num_gpu"] = 0

            response = self.client.generate(
                model=self.model,
                prompt=full_prompt,
                stream=False,
                options=options,
            )
            
            result = response.get("response", "").strip()
            logger.debug(f"[LLM Response] Tokens: {len(result.split())}")
            return result
            
        except Exception as e:
            logger.error(f"Ollama invocation failed: {e}")
            logger.info("Falling back to mock response mode")
            self.fallback_mode = True
            return self._get_fallback_response(prompt, system_prompt)
    
    def _invoke_litellm(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Invoke remote LLM via LiteLLM."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.litellm.completion(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.api_key
            )
            
            result = response.choices[0].message.content.strip()
            logger.debug(f"[LLM Response] Tokens: {len(result.split())}")
            return result
            
        except Exception as e:
            logger.error(f"LiteLLM invocation failed: {e}")
            logger.info("Falling back to mock response mode")
            self.fallback_mode = True
            return self._get_fallback_response(prompt, system_prompt)
    
    def _get_fallback_response(self, prompt: str, system_prompt: Optional[str]) -> str:
        """
        Return mock response based on prompt keywords.
        Useful for MVP testing without LLM dependency.
        """
        prompt_lower = prompt.lower()
        
        # Route based on detected keywords
        if "terrain" in prompt_lower or "slope" in prompt_lower:
            return json.dumps({
                "analysis": "Terrain analysis complete",
                "slope_risk": "moderate",
                "terrain_type": "rocky",
                "traversability": 0.7,
                "recommendation": "Reduce speed by 20%"
            })
        
        elif "wind" in prompt_lower:
            return json.dumps({
                "analysis": "Wind analysis complete",
                "wind_risk": "low",
                "gust_safety": "safe",
                "recommendation": "Proceed with caution"
            })
        
        elif "obstacle" in prompt_lower:
            return json.dumps({
                "obstacles_detected": 2,
                "avoidance_priority": "high",
                "recommendation": "Route around boulders to northeast"
            })
        
        elif "plan" in prompt_lower or "route" in prompt_lower:
            return json.dumps({
                "route_generated": True,
                "waypoints": 3,
                "estimated_duration_s": 600,
                "success_probability": 0.85,
                "recommendation": "Execute planned route"
            })
        
        elif "action" in prompt_lower or "movement" in prompt_lower:
            return json.dumps({
                "action": "move_forward",
                "recommended_speed": 0.3,
                "heading_adjustment": 5,
                "recommendation": "Execute movement at reduced speed"
            })
        
        elif "memory" in prompt_lower or "experience" in prompt_lower:
            return json.dumps({
                "experience_stored": True,
                "patterns_learned": 1,
                "recommendation": "Similar terrain encountered. Use learned strategy."
            })
        
        else:
            # Generic fallback
            return json.dumps({
                "status": "success",
                "analysis": "Analysis complete",
                "recommendation": "Proceed with caution"
            })
    
    def health_check(self) -> bool:
        """Check if LLM is available."""
        if self.fallback_mode:
            return False
        
        try:
            if self.use_local and self.client:
                # Try a simple test call
                response = self.client.generate(
                    model=self.model,
                    prompt="test",
                    stream=False
                )
                return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get LLM client statistics."""
        return {
            "model": self.model,
            "invocation_count": self.invocation_count,
            "fallback_mode": self.fallback_mode,
            "use_local": self.use_local,
            "timestamp": datetime.now().isoformat()
        }


# Singleton instance
_llama_instance: Optional[LlamaClient] = None


def get_llama_client(
    model: str = "llama2",
    base_url: str = "http://localhost:11434",
    use_local: bool = True,
    fallback_mode: bool = False
) -> LlamaClient:
    """
    Get or create singleton LlamaClient instance.
    
    Args:
        model: Model name
        base_url: Ollama/LiteLLM endpoint
        use_local: Use local Ollama
        fallback_mode: Use mock responses
        
    Returns:
        LlamaClient instance
    """
    global _llama_instance
    if _llama_instance is None:
        _llama_instance = LlamaClient(
            model=model,
            base_url=base_url,
            use_local=use_local,
            fallback_mode=fallback_mode
        )
    return _llama_instance
