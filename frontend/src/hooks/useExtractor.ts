import { useState } from "react";
import { api } from "../services/api";
import type { ExtractResponse, VerifiedElement, Filters, ExtractedElement } from "../types";

export function useExtractor() {
  const [htmlInput, setHtmlInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [results, setResults] = useState<ExtractResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verifications, setVerifications] = useState<VerifiedElement[] | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [inputExpanded, setInputExpanded] = useState(false);
  const [isSessionActive, setIsSessionActive] = useState(false);

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

  const handleExtractURL = async (resetFilters: (filters: Filters) => void) => {
    if (!urlInput.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);
    setVerifications(null);
    resetFilters({ search: "", mode: "All", elementType: "All", stableOnly: false, minScore: 0 });
    try {
      const data = await api.extractLocatorsFromUrl(urlInput);
      setResults(data);
      setInputExpanded(false);
    } catch (err: any) {
      setError(err.message ?? "URL Extraction failed. Ensure the URL is accessible.");
    } finally {
      setLoading(false);
    }
  };

  const handleStartSession = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.startSession(urlInput || "https://google.com");
      setIsSessionActive(true);
    } catch (err: any) {
      setError(err.message ?? "Failed to start browser session.");
    } finally {
      setLoading(false);
    }
  };

  const handleCaptureSession = async (resetFilters: (filters: Filters) => void) => {
    setLoading(true);
    setError(null);
    setVerifications(null);
    resetFilters({ search: "", mode: "All", elementType: "All", stableOnly: false, minScore: 0 });
    try {
      const data = await api.captureSession();
      setResults(data);
    } catch (err: any) {
      setError(err.message ?? "Failed to capture current page.");
    } finally {
      setLoading(false);
    }
  };

  const handleStopSession = async () => {
    try {
      await api.stopSession();
      setIsSessionActive(false);
    } catch (err: any) {
      console.error("Failed to stop session", err);
    }
  };

  const handleHighlight = async (element: ExtractedElement) => {
    if (!isSessionActive) return;
    try {
      await api.highlightElement(
        element.recommended_locator.strategy,
        element.recommended_locator.value,
        element.absolute_xpath // Using absolute_xpath as internal_xpath
      );
    } catch (err: any) {
      console.error("Highlight failed", err);
    }
  };

  const handleVerify = async (setToast: (msg: string) => void) => {
    if (!results) return;

    setVerifying(true);
    try {
      if (isSessionActive) {
        // Deep verification in live browser
        const data = await api.verifySessionLocators(results.elements);
        
        // Update the results with verified elements (including those with broken locators)
        setResults(prev => prev ? {
           ...prev,
           elements: data.elements,
           total_elements: data.total_elements,
           stable_elements: data.stable_elements
        } : null);
        
        setToast(`Live verification complete. ${data.stable_elements} stable elements found.`);
      } else {
        // Standard static verification
        const htmlToVerify = htmlInput || (results as any).html; 
        if (!htmlToVerify) {
            setToast("Verification requires HTML content.");
            setVerifying(false);
            return;
        }
        const data = await api.verifyLocators(htmlToVerify, results.elements);
        setVerifications(data.verified_elements);
        setToast(`Verification complete: ${data.summary.correct_locators} correct.`);
      }
    } catch (err: any) {
      setToast(`Verification failed: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  const handleReset = (resetFilters: (filters: Filters) => void) => {
    setHtmlInput("");
    setUrlInput("");
    setResults(null);
    setError(null);
    setVerifications(null);
    setInputExpanded(false);
    resetFilters({ search: "", mode: "All", elementType: "All", stableOnly: false, minScore: 0 });
  };

  return {
    htmlInput,
    setHtmlInput,
    urlInput,
    setUrlInput,
    results,
    loading,
    error,
    verifications,
    verifying,
    inputExpanded,
    setInputExpanded,
    handleExtract,
    handleExtractURL,
    handleStartSession,
    handleCaptureSession,
    handleStopSession,
    handleHighlight,
    handleVerify,
    handleReset,
    isSessionActive,
  };
}
