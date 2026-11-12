from dataclasses import dataclass
import re
from time import monotonic

@dataclass
class Goal:
    target_score: int | None
    minutes: float | None
    started_at: float
    accuracy_priority: str = 'high'

    @classmethod
    def create(cls, target_score, minutes):
        if target_score is not None and not 0 <= target_score <= 100:
            raise ValueError('target-score must be between 0 and 100')
        if minutes is not None and minutes <= 0:
            raise ValueError('minutes must be positive')
        return cls(target_score, minutes, monotonic())

    @classmethod
    def parse(cls, text):
        score = re.search(r'(?:smartscore|score|分数|得分)\s*(\d+)', text, re.I)
        duration = re.search(r'(\d+(?:\.\d+)?)\s*(minutes?|mins?|分钟|seconds?|secs?|秒)', text, re.I)
        target = int(score[1]) if score else (100 if re.search(r'complete|完成', text, re.I) else None)
        minutes = float(duration[1]) / (60 if re.match(r's|秒', duration[2], re.I) else 1) if duration else None
        if target is None and minutes is None:
            raise ValueError('Specify a SmartScore target, completion, or a time limit')
        return cls.create(target, minutes)

    @property
    def seconds_left(self):
        return float('inf') if self.minutes is None else max(0, self.minutes*60-(monotonic()-self.started_at))

    @property
    def expired(self):
        return self.seconds_left <= 0

    def reached(self, score):
        return score is not None and self.target_score is not None and score >= self.target_score
