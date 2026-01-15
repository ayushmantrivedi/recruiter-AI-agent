from typing import List, Optional
import re
from dataclasses import dataclass

@dataclass
class ParsedQuery:
    raw: str
    normalized: str
    tokens: List[str]

class QueryParser:
    @staticmethod
    def parse(query: str) -> ParsedQuery:
        """
        Normalize text, tokenize, and return ParsedQuery object.
        """
        raw = query
        normalized = query.lower().strip()
        
        # Remove special characters but keep alphanumeric and spaces
        # keeping + for experience (e.g., 4+)
        normalized = re.sub(r'[^a-z0-9\s\+]', '', normalized)
        
        tokens = normalized.split()
        
        return ParsedQuery(
            raw=raw,
            normalized=normalized,
            tokens=tokens
        )
