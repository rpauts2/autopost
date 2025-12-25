"""Content banality filter - removes cliches and obvious topics."""

from typing import Dict, Any, Optional, List
import re

from utils.logger import get_logger
from utils.helpers import get_timestamp

logger = get_logger(__name__)


class BanalityFilter:
    """Filters out banal and cliched content."""
    
    def __init__(self):
        self.logger = logger
        # Common cliches and banal phrases (Russian)
        self.cliches = [
            r'\bв\s+наше\s+время\b',
            r'\bкак\s+известно\b',
            r'\bне\s+секрет[,\s]что\b',
            r'\bвсе\s+знают\b',
            r'\bочевидно\b',
            r'\bбезусловно\b',
            r'\bконечно\b',
            r'\bнесомненно\b',
            r'\bкак\s+правило\b',
            r'\bобычно\b',
            r'\bтрадиционно\b',
            r'\bкак\s+всегда\b',
            r'\bсегодня\s+каждый\b',
            r'\bв\s+современном\s+мире\b',
            r'\bсовременное\s+общество\b',
            r'\bнадо\s+задуматься\b',
            r'\bстоит\s+задуматься\b',
            r'\bдавайте\s+задумаемся\b',
            r'\bвсе\s+изменилось\b',
            r'\bвсе\s+стало\s+другим\b',
            r'\bжизнь\s+не\s+стоит\s+на\s+месте\b',
            r'\bвремя\s+не\s+стоит\s+на\s+месте\b',
        ]
        
        # Obvious topics that should be avoided
        self.obvious_topics = [
            'как начать',
            'топ 10',
            'лучшие способы',
            'секреты успеха',
            'как стать',
            'простые советы',
            'что нужно знать',
            'все о',
            'руководство для начинающих',
        ]
        
        # Empty thoughts patterns
        self.empty_patterns = [
            r'\bважно\s+помнить\b',
            r'\bнужно\s+понимать\b',
            r'\bследует\s+знать\b',
            r'\bстоит\s+отметить\b',
            r'\bобратим\s+внимание\b',
        ]
    
    def check_banality(self, content: str, topic: str = "") -> Dict[str, Any]:
        """Check content for banality and cliches."""
        result = {
            "is_banal": False,
            "banality_score": 0.0,
            "issues": [],
            "cliche_count": 0,
            "empty_phrases_count": 0,
        }
        
        content_lower = content.lower()
        topic_lower = topic.lower() if topic else ""
        
        # Check for cliches
        cliche_count = 0
        found_cliches = []
        for cliche in self.cliches:
            matches = len(re.findall(cliche, content_lower))
            if matches > 0:
                cliche_count += matches
                found_cliches.append(cliche)
        
        result["cliche_count"] = cliche_count
        if cliche_count > 0:
            result["issues"].append(f"Найдено клише: {cliche_count}")
        
        # Check for obvious topics
        obvious_count = 0
        for obvious in self.obvious_topics:
            if obvious in topic_lower or obvious in content_lower:
                obvious_count += 1
                result["issues"].append(f"Очевидная тема: {obvious}")
        
        # Check for empty phrases
        empty_count = 0
        for pattern in self.empty_patterns:
            matches = len(re.findall(pattern, content_lower))
            empty_count += matches
        
        result["empty_phrases_count"] = empty_count
        if empty_count > 0:
            result["issues"].append(f"Пустые фразы: {empty_count}")
        
        # Calculate banality score (0.0 - 1.0)
        # Normalize by content length
        content_length = len(content.split())
        if content_length > 0:
            cliche_score = min(1.0, cliche_count / max(1, content_length / 50))  # 1 cliche per 50 words = high
            empty_score = min(1.0, empty_count / max(1, content_length / 30))  # 1 empty per 30 words = high
            obvious_score = 1.0 if obvious_count > 0 else 0.0
            
            result["banality_score"] = max(cliche_score, empty_score, obvious_score * 0.8)
        
        # Threshold for banal content
        result["is_banal"] = result["banality_score"] > 0.3
        
        if result["is_banal"]:
            result["issues"].append(f"Общий показатель банальности: {result['banality_score']:.2f}")
        
        return result
    
    def should_reject(self, content: str, topic: str = "") -> tuple[bool, str]:
        """Determine if content should be rejected due to banality."""
        check = self.check_banality(content, topic)
        
        if check["is_banal"]:
            reason = "; ".join(check["issues"])
            return True, f"Контент слишком банальный: {reason}"
        
        return False, ""
    
    def improve_content(self, content: str, banality_issues: List[str]) -> str:
        """Attempt to improve content by removing banal elements."""
        improved = content
        
        # Remove common cliches (basic replacement)
        for cliche_pattern in self.cliches:
            # Simple removal - in production would use AI for better replacement
            improved = re.sub(cliche_pattern, '', improved, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        improved = re.sub(r'\s+', ' ', improved).strip()
        
        return improved


class SemanticDensityChecker:
    """Checks semantic density of content."""
    
    def __init__(self):
        self.logger = logger
    
    def calculate_density(self, content: str) -> float:
        """Calculate semantic density (0.0 - 1.0)."""
        if not content:
            return 0.0
        
        words = content.split()
        if len(words) < 10:
            return 0.0
        
        # Simple heuristics for semantic density
        # High density = unique words, low repetition, substantial content
        
        unique_words = len(set(words))
        total_words = len(words)
        uniqueness_ratio = unique_words / total_words if total_words > 0 else 0
        
        # Average word length (longer words often = more specific)
        avg_word_length = sum(len(w) for w in words) / total_words if total_words > 0 else 0
        length_score = min(1.0, avg_word_length / 7.0)  # 7 chars average = good
        
        # Sentence count (more sentences = more structure)
        sentences = re.split(r'[.!?]+', content)
        sentence_count = len([s for s in sentences if s.strip()])
        sentence_score = min(1.0, sentence_count / 5.0)  # 5 sentences = good
        
        # Combined score
        density = (uniqueness_ratio * 0.4 + length_score * 0.3 + sentence_score * 0.3)
        
        return min(1.0, density)
    
    def is_dense_enough(self, content: str, threshold: float = 0.4) -> tuple[bool, float]:
        """Check if content has sufficient semantic density."""
        density = self.calculate_density(content)
        return density >= threshold, density

