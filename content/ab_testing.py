"""Content A/B testing - выбор лучшей формулировки."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from utils.logger import get_logger
from utils.helpers import get_timestamp

logger = get_logger(__name__)


@dataclass
class ABVariant:
    """A/B test variant."""
    id: str
    content: str
    created_at: str
    metadata: Dict[str, Any]


class ABTester:
    """Manages A/B testing of content formulations."""
    
    def __init__(self, ai_router=None):
        self.ai_router = ai_router
        self.logger = logger
    
    async def create_variants(
        self,
        base_idea: str,
        topic: str,
        count: int = 2
    ) -> List[ABVariant]:
        """Create multiple variants of content for the same idea."""
        if not self.ai_router:
            return []
        
        from utils.helpers import generate_id
        
        variants = []
        
        for i in range(count):
            prompt = f"""Создай вариант формулировки этой идеи:

Идея: {base_idea}
Тема: {topic}

Вариант {i+1}: создай уникальную формулировку той же идеи, но с другим подходом:
- Разный стиль подачи
- Разная структура
- Разные акценты
- Разная длина (если возможно)

Ответь только текстом варианта, без комментариев."""

            try:
                content = await self.ai_router.generate(
                    prompt=prompt,
                    task_type="default"
                )
                
                variant = ABVariant(
                    id=generate_id(f"variant_{i}_"),
                    content=content,
                    created_at=get_timestamp(),
                    metadata={"variant_number": i+1, "topic": topic}
                )
                variants.append(variant)
            except Exception as e:
                self.logger.error(f"Error creating variant {i+1}: {e}")
        
        return variants
    
    async def evaluate_variants(
        self,
        variants: List[ABVariant],
        criteria: List[str] = None
    ) -> Tuple[ABVariant, Dict[str, Any]]:
        """Evaluate variants and select best one."""
        if not variants:
            raise ValueError("No variants to evaluate")
        
        if len(variants) == 1:
            return variants[0], {"reason": "Only one variant"}
        
        if not self.ai_router:
            # Fallback: return first variant
            return variants[0], {"reason": "AI router not available"}
        
        criteria = criteria or [
            "ясность мысли",
            "оригинальность формулировки",
            "глубина раскрытия",
            "логичность структуры",
            "общая убедительность"
        ]
        
        # Prepare evaluation prompt
        variants_text = "\n\n".join([
            f"ВАРИАНТ {i+1}:\n{v.content[:500]}"
            for i, v in enumerate(variants)
        ])
        
        prompt = f"""Оцени варианты формулировки одной и той же идеи.

Критерии оценки:
{chr(10).join(f"- {c}" for c in criteria)}

Варианты:
{variants_text}

Ответь в формате JSON:
{{
    "best_variant": 1-{len(variants)},
    "reasoning": "обоснование выбора",
    "scores": {{
        "variant_1": {{"score": 0.0-1.0, "strengths": ["..."], "weaknesses": ["..."]}},
        ...
    }}
}}"""

        try:
            response = await self.ai_router.generate(
                prompt=prompt,
                task_type="deep_analysis",
                system_instruction="Ты эксперт по оценке качества формулировок. Будь объективен и критичен."
            )
            
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
                best_num = evaluation.get("best_variant", 1)
                best_index = best_num - 1  # Convert to 0-based
                
                if 0 <= best_index < len(variants):
                    best_variant = variants[best_index]
                    evaluation_data = {
                        "reasoning": evaluation.get("reasoning", ""),
                        "scores": evaluation.get("scores", {})
                    }
                    return best_variant, evaluation_data
        except Exception as e:
            self.logger.error(f"Error evaluating variants: {e}")
        
        # Fallback
        return variants[0], {"reason": "Evaluation failed, using first variant"}

