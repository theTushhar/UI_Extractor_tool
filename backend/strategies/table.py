from lxml.html import HtmlElement
from core.models import RawCandidate
from utils.html import xpath_literal
from utils.text import normalize_space_text
from strategies.base import LocatorStrategy

class TableStrategy(LocatorStrategy):
    """
    Generates locators for elements inside tables based on row and column context.
    """
    
    def generate(self, el: HtmlElement, root: HtmlElement) -> list[RawCandidate]:
        candidates = []
        
        # Check if element is inside a table
        td_ancestors = el.xpath("ancestor::td[1] | ancestor::th[1]")
        if not td_ancestors:
            return candidates
            
        td = td_ancestors[0]
        tr_ancestors = td.xpath("ancestor::tr[1]")
        if not tr_ancestors:
            return candidates
            
        tr = tr_ancestors[0]
        table_ancestors = tr.xpath("ancestor::table[1]")
        if not table_ancestors:
            return candidates
            
        # 1) Row Text Context
        # Find a stable text in the current row to use as an anchor
        row_cells = tr.xpath(".//td | .//th")
        anchor_text = ""
        for cell in row_cells:
            if cell == td: continue
            text = normalize_space_text(" ".join(cell.itertext()))
            if text and 1 < len(text) < 50:
                anchor_text = text
                break
        
        tag = el.tag.lower()
        if anchor_text:
            # XPath: find row containing anchor_text, then find the element tag inside it
            # Using normalize-space(.) instead of contains for more precision if possible
            xpath_val = f"//tr[descendant::*[normalize-space(.)={xpath_literal(anchor_text)}]]//{tag}"
            candidates.append(RawCandidate(
                strategy="xpath:table_row_anchor",
                value=xpath_val,
                internal_xpath=xpath_val,
                base_score=82,
                intended_stable=True,
                rationale=f"Locates {tag} in a row containing the text '{anchor_text}'."
            ))

        # 2) Column Header Context
        cell_index = len(td.xpath("preceding-sibling::td | preceding-sibling::th"))
        # Try to find headers in the same table
        table = table_ancestors[0]
        headers = table.xpath(".//thead//th | .//tr[1]//th")
        
        if headers and cell_index < len(headers):
            header_text = normalize_space_text(" ".join(headers[cell_index].itertext()))
            if header_text and anchor_text:
                # Advanced XPath: Row anchor + Column header index mapping
                xpath_val = f"//tr[descendant::*[normalize-space(.)={xpath_literal(anchor_text)}]]/td[count(//th[normalize-space(.)={xpath_literal(header_text)}]/preceding-sibling::th)+1]//{tag}"
                candidates.append(RawCandidate(
                    strategy="xpath:table_row_column_anchor",
                    value=xpath_val,
                    internal_xpath=xpath_val,
                    base_score=88,
                    intended_stable=True,
                    rationale=f"Locates {tag} in the '{header_text}' column of the row containing '{anchor_text}'."
                ))

        return candidates
