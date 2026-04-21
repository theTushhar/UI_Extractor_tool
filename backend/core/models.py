from dataclasses import dataclass, field

@dataclass
class RawCandidate:
    strategy: str
    value: str
    base_score: int
    intended_stable: bool
    rationale: str
    internal_xpath: str = field(default="")

@dataclass
class Locator:
    strategy: str
    value: str
    unique: bool
    stable: bool
    score: int
    risk_level: str
    rationale: str
    internal_xpath: str = field(default="")
