// Matches backend schemas.py exactly

export interface LocatorCandidate {
  rank: number;
  strategy: string;
  value: string;
  unique: boolean;
  score: number;
}

export interface RecommendedLocator {
  strategy: string;
  value: string;
  score: number;
  reason: string;
}

export type ElementMode = "Input" | "Output" | "UserAction" | "Unknown";

export interface ExtractedElement {
  tag: string;
  element_name: string;
  mode: ElementMode;
  element_type: string;
  attributes: Record<string, string>;
  recommended_locator: RecommendedLocator;
  locators: LocatorCandidate[];
}

export interface ExtractResponse {
  page_name: string;
  total_elements: number;
  stable_elements: number;
  elements: ExtractedElement[];
}

export type SortField = "element_name" | "element_type" | "mode" | "score" | "locators";
export type SortDir = "asc" | "desc";

export interface Filters {
  search: string;
  mode: string;        // "All" | ElementMode
  elementType: string; // "All" | specific type
  stableOnly: boolean;
}
