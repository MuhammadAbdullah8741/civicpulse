from app.providers.triage.base import TriageResult
from app.schemas import Category, Priority


class RuleBasedTriage:
    name = "rules"

    def triage(self, text: str, location: str) -> TriageResult:
        content = text.lower()
        keywords = {
            Category.STREETLIGHTS: ("streetlight", "street light"),
            Category.SANITATION: ("sewage", "kachra", "rubbish", "garbage", "drain"),
            Category.WATER: ("water", "pipe", "tanker"),
            Category.ELECTRICITY: ("electricity", "voltage", "transformer", "wire"),
            Category.ROADS: ("pothole", "road", "manhole", "crossing"),
        }
        category = next(
            (
                category
                for category, words in keywords.items()
                if any(word in content for word in words)
            ),
            Category.OTHER,
        )
        urgent = (
            "flood", "burst", "live wire", "live electricity wire",
            "sparks", "accident", "uncovered manhole", "entering houses",
        )
        priority = (
            Priority.HIGH
            if any(word in content for word in urgent)
            else Priority.NORMAL
        )
        return TriageResult(
            category=category,
            priority=priority,
            summary=" ".join(text.split())[:140],
            confidence=0.5,
        )
