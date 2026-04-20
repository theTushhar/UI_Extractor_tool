import { useState } from "react";
import { api } from "../services/api";
import type { ExtractResponse, VerifiedElement, Filters } from "../types";

export function useExtractor() {
  const [htmlInput, setHtmlInput] = useState("");
  const [results, setResults] = useState<ExtractResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verifications, setVerifications] = useState<VerifiedElement[] | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [inputExpanded, setInputExpanded] = useState(false);

  const handleExtract = async (resetFilters: (filters: Filters) => void) => {
    if (!htmlInput.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);
    setVerifications(null);
    resetFilters({ search: "", mode: "All", elementType: "All", stableOnly: false, minScore: 0 });
    try {
      const data = await api.extractLocators(htmlInput);
      setResults(data);
      setInputExpanded(false);
    } catch (err: any) {
      setError(err.message ?? "Extraction failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (setToast: (msg: string) => void) => {
    if (!results || !htmlInput) return;
    setVerifying(true);
    try {
      const data = await api.verifyLocators(htmlInput, results.elements);
      setVerifications(data.verified_elements);
      setToast(`Verification complete: ${data.summary.correct_locators} correct, ${data.summary.broken_locators} broken`);
    } catch (err: any) {
      setToast(`Verification failed: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  const handleReset = (resetFilters: (filters: Filters) => void) => {
    setHtmlInput("");
    setResults(null);
    setError(null);
    setVerifications(null);
    setInputExpanded(false);
    resetFilters({ search: "", mode: "All", elementType: "All", stableOnly: false, minScore: 0 });
  };

  return {
    htmlInput,
    setHtmlInput,
    results,
    loading,
    error,
    verifications,
    verifying,
    inputExpanded,
    setInputExpanded,
    handleExtract,
    handleVerify,
    handleReset,
  };
}
