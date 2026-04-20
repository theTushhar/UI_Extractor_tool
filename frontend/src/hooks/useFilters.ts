import { useState, useMemo } from "react";
import type { ExtractResponse, Filters } from "../types";

export function useFilters(results: ExtractResponse | null) {
  const [filters, setFilters] = useState<Filters>({
    search: "",
    mode: "All",
    elementType: "All",
    stableOnly: false,
    minScore: 0,
  });

  const availableTypes = useMemo(
    () => [...new Set(results?.elements.map((e) => e.element_type) ?? [])].sort(),
    [results]
  );

  const filteredCount = useMemo(() => {
    if (!results) return 0;
    return results.elements.filter((el) => {
      if (filters.search) {
        const q = filters.search.toLowerCase();
        const match =
          el.element_name.toLowerCase().includes(q) ||
          el.element_type.toLowerCase().includes(q) ||
          el.recommended_locator.value.toLowerCase().includes(q);
        if (!match) return false;
      }
      if (filters.mode !== "All" && el.mode !== filters.mode) return false;
      if (filters.elementType !== "All" && el.element_type !== filters.elementType) return false;
      if (filters.stableOnly && el.recommended_locator.score < 80) return false;
      if (el.recommended_locator.score < filters.minScore) return false;
      return true;
    }).length;
  }, [results, filters]);

  return {
    filters,
    setFilters,
    availableTypes,
    filteredCount,
  };
}
