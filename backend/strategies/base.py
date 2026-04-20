from abc import ABC, abstractmethod
from lxml.html import HtmlElement
from core.models import RawCandidate

class LocatorStrategy(ABC):
    @abstractmethod
    def generate(self, el: HtmlElement, root: HtmlElement) -> list[RawCandidate]:
        pass
