from dataclasses import dataclass

@dataclass
class RawCandidate:
    strategy: str
    value: str
    base_score: int
    intended_stable: bool
    rationale: str

@dataclass
class Locator:
    strategy: str
    value: str
    unique: bool
    stable: bool
    score: int
    risk_level: str
    rationale: str
