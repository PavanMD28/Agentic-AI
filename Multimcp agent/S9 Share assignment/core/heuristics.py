import re
from typing import Tuple, List

# Constants
_BRACKETED_MESSAGE_PATTERN = re.compile(r"\[.*\]")
_UNSUCCESSFUL_OUTPUT_PREFIXES = {
    "Unexpected result format from agent:",
    "Max steps reached",
}

# Default bad words for censoring
DEFAULT_BAD_WORDS = {
    "Bastard", "Pissed", "Craphead", "Dang"
}

class TextValidation:
    """Collection of text validation heuristics."""
    
    @staticmethod
    def is_valid_agent_output(text: str) -> bool:
        """
        Heuristic (ID: H001)
        Checks if the agent's output text is valid and not a system error/status message.
        """
        if not text:
            return False
        if _BRACKETED_MESSAGE_PATTERN.fullmatch(text):
            return False
        return not any(text.startswith(prefix) for prefix in _UNSUCCESSFUL_OUTPUT_PREFIXES)

    @staticmethod
    def is_within_length_limits(text: str, min_length: int = 0, max_length: int = 10240) -> bool:
        """
        Heuristic (ID: H005)
        Checks if text length is within specified limits.
        """
        if not isinstance(text, str):
            return False
        length = len(text)
        return min_length <= length <= max_length

    @staticmethod
    def contains_no_digits(text: str) -> bool:
        """
        Heuristic (ID: H006)
        Checks if text contains no digit characters.
        """
        if not isinstance(text, str):
            return True
        return not any(char.isdigit() for char in text)

    @staticmethod
    def is_positive_integer_string(text: str) -> bool:
        """
        Heuristic (ID: H007)
        Validates if string represents a positive integer.
        """
        if not isinstance(text, str):
            return False
        return text.isdigit() and int(text) > 0

    @staticmethod
    def is_not_empty_or_whitespace(text: str) -> bool:
        """
        Heuristic (ID: H008)
        Checks if string has non-whitespace content.
        """
        return isinstance(text, str) and text.strip() != ""

    @staticmethod
    def has_balanced_brackets(text: str, open_char: str = '(', close_char: str = ')') -> bool:
        """
        Heuristic (ID: H009)
        Checks for balanced bracket pairs.
        """
        if not isinstance(text, str):
            return True
        
        balance = 0
        for char in text:
            if char == open_char:
                balance += 1
            elif char == close_char:
                balance -= 1
            if balance < 0:
                return False
        return balance == 0

class SecurityValidation:
    """Collection of security-related validation heuristics."""
    
    @staticmethod
    def check_url_is_secure(url_string: str) -> bool:
        """
        Heuristic (ID: H002)
        Validates if URL uses HTTPS protocol.
        """
        if not isinstance(url_string, str):
            return False
        return url_string.strip().lower().startswith("https://")

    @staticmethod
    def is_valid_email_format(email_string: str) -> bool:
        """
        Heuristic (ID: H004)
        Validates basic email format.
        """
        if not isinstance(email_string, str):
            return False
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        return bool(email_pattern.fullmatch(email_string))

    @staticmethod
    def censor_bad_words(text: str, custom_bad_words: set = None, replacement: str = "***") -> str:
        """
        Heuristic (ID: H003)
        Censors specified bad words in text.
        """
        if not isinstance(text, str):
            return ""

        combined_bad_words = DEFAULT_BAD_WORDS.copy()
        if custom_bad_words:
            combined_bad_words.update(word.lower() for word in custom_bad_words)

        if not combined_bad_words:
            return text

        try:
            valid_bad_words = [word for word in combined_bad_words if word]
            if not valid_bad_words:
                return text
            pattern_str = r'\b(' + '|'.join(re.escape(word) for word in sorted(valid_bad_words, key=len, reverse=True)) + r')\b'
            pattern = re.compile(pattern_str, flags=re.IGNORECASE)
            return pattern.sub(replacement, text)
        except re.error as e:
            print(f"Regex error in censor_bad_words: {e}. Returning original text.")
            return text

class SystemValidation:
    """Collection of system-related validation heuristics."""
    
    @staticmethod
    def is_allowed_tool_name(tool_name: str, allowed_tools_registry: set) -> bool:
        """
        Heuristic (ID: H010)
        Validates if tool name is in allowed registry.
        """
        if not isinstance(tool_name, str) or not isinstance(allowed_tools_registry, set):
            return False
        return tool_name in allowed_tools_registry

    @staticmethod
    def check_retry_limit(current_attempts: int, max_attempts: int = 3) -> bool:
        """
        Heuristic (ID: H011)
        Checks if retry attempts are within limit.
        """
        if not (isinstance(current_attempts, int) and isinstance(max_attempts, int)):
            return False
        return current_attempts < max_attempts

class QueryHeuristics:
    """Applies safety and preprocessing heuristics to user queries."""
    
    def __init__(self):
        self.unsafe_patterns = [
            r"(?i)(rm|remove|del|delete)\s+-rf?\s+[\/\*]",
            r"(?i)sudo\s+",
            r"(?i)(chmod|chown)\s+777",
            r"(?i)>(>?)\s*/dev/(null|zero|random)",
            r"(?i)eval\s*\(",
            r"(?i)exec\s*\(",
            r"(?i)system\s*\(",
            r"(?i)(?:drop|delete)\s+(?:table|database)",
            r"(?i)(?:truncate|alter)\s+table",
            r"(?i)(?:update|insert)\s+(?:into\s+)?[a-zA-Z_][a-zA-Z0-9_]*\s+set",
            r"(?i)\/etc\/(?:passwd|shadow|hosts)",
            r"(?i)(?:\.env|config\.php|wp-config\.php)",
        ]
        
        self.sanitize_patterns = [
            (r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", ""),
            (r"(?i)javascript:", ""),
            (r"(?i)data:", ""),
            (r"(?i)vbscript:", ""),
            (r"<[^>]*>", ""),
            (r"(?i)on\w+\s*=", ""),
            (r"(?i)expression\s*\(", ""),
            (r"(?i)url\s*\(", "url("),
            (r"\s+", " "),
        ]

    def _contains_unsafe_pattern(self, query: str) -> bool:
        """Check if query contains unsafe patterns."""
        return any(re.search(pattern, query) for pattern in self.unsafe_patterns)

    def _sanitize_input(self, query: str) -> str:
        """Apply input sanitization."""
        result = query.strip()
        for pattern, replacement in self.sanitize_patterns:
            result = re.sub(pattern, replacement, result)
        return result.strip()

    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent processing."""
        query = re.sub(r'\s+', ' ', query.strip())
        query = re.sub(r'^(?:please|hey|hi|could you|can you)\s+', '', query, flags=re.IGNORECASE)
        return query

    def process_query(self, query: str) -> Tuple[str, bool]:
        """Process query through all heuristics."""
        if not query or not isinstance(query, str):
            return "", False

        if self._contains_unsafe_pattern(query):
            return query, False

        sanitized = self._sanitize_input(query)
        if not sanitized:
            return "", False

        normalized = self._normalize_query(sanitized)
        if not normalized:
            return "", False

        return normalized, True

    def get_safety_rules(self) -> List[str]:
        """Return enforced safety rules."""
        return [
            "No dangerous system commands (rm -rf, chmod 777, etc.)",
            "No direct system access commands (sudo)",
            "No dangerous SQL operations (DROP, DELETE, etc.)",
            "No access to sensitive system files",
            "No dangerous function calls (eval, exec, system)",
            "No HTML/JavaScript injection",
            "No access to sensitive configuration files",
            "Input must be properly sanitized",
            "Input must not contain control characters",
            "Input must be properly normalized"
        ]
