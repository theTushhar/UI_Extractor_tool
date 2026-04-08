import { useState } from "react";
import { api } from "./api";

function App() {
  const [htmlInput, setHtmlInput] = useState("");
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleExtract = async () => {
    if (!htmlInput.trim()) return;
    setLoading(true);
    setResults(null);
    try {
      const data = await api.extractLocators(htmlInput);
      setResults(data);
    } catch (err: any) {
      console.error(err);
      setResults({ error: "Extraction failed: " + err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container is-fluid" style={{ minHeight: "100vh", padding: "40px 16px" }}>
      {/* HEADER */}
      <div className="has-text-centered mb-6">
        <h1 className="title is-2 has-text-info has-text-weight-bold">
          🤖 Static UI Extractor
        </h1>
        <p className="subtitle is-6 has-text-grey-light">
          Paste your raw HTML and get robust, deterministic UI locators instantly.
        </p>
      </div>

      <div className="columns is-centered">
        <div className="column is-8">
          {/* INPUT CARD */}
          <div className="card has-background-dark-ter mb-6" style={{ borderRadius: '12px', border: '1px solid #363636' }}>
            <div className="card-content">
              <div className="field">
                <label className="label has-text-grey-light">Raw HTML Source</label>
                <div className="control">
                  <textarea
                    className="textarea is-dark is-family-monospace"
                    rows={12}
                    value={htmlInput}
                    onChange={(e) => setHtmlInput(e.target.value)}
                    placeholder="<html><body><button id='login'>Login</button></body></html>"
                    style={{ backgroundColor: '#121212', color: '#e0e0e0', border: '1px solid #4a4a4a' }}
                  />
                </div>
              </div>

              <div className="level mt-5">
                <div className="level-left">
                  <div className="tags has-addons">
                    <span className="tag is-dark">Mode</span>
                    <span className="tag is-info">Deterministic Parser</span>
                  </div>
                </div>
                <div className="level-right">
                  <button
                    className={`button is-info is-medium has-text-weight-bold ${loading ? "is-loading" : ""}`}
                    onClick={handleExtract}
                    disabled={!htmlInput.trim() || loading}
                    style={{ minWidth: '200px' }}
                  >
                    <span>Extract Locators</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* RESULTS AREA */}
          {results && (
            <div className="animate__animated animate__fadeIn">
              <div className="level mb-4">
                <div className="level-left">
                  <h2 className="title is-4 has-text-light">
                    📊 Extraction Report
                  </h2>
                </div>
                <div className="level-right">
                  {results.elements && (
                    <div className="tags has-addons">
                      <span className="tag is-dark">Elements</span>
                      <span className="tag is-success">{results.total_elements} Found</span>
                      <span className="tag is-info">{results.stable_elements} Stable</span>
                    </div>
                  )}
                </div>
              </div>

              {results.error ? (
                <article className="message is-danger">
                  <div className="message-body">
                    <strong>Error:</strong> {results.error}
                  </div>
                </article>
              ) : (
                <div className="box has-background-dark-ter p-0" style={{ border: '1px solid #363636', overflow: 'hidden' }}>
                  <table className="table is-fullwidth is-hoverable has-background-dark has-text-light m-0">
                    <thead>
                      <tr style={{ borderBottom: '2px solid #363636' }}>
                        <th className="has-text-grey-light py-4 pl-5">Element Name</th>
                        <th className="has-text-grey-light py-4">Recommended Locator</th>
                        <th className="has-text-grey-light py-4">Strategy</th>
                        <th className="has-text-grey-light py-4 pr-5 has-text-centered">Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.elements.map((el: any, idx: number) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #363636' }}>
                          <td className="py-4 pl-5">
                            <span className="has-text-weight-semibold">{el.element_name}</span>
                            <br />
                            <small className="has-text-grey">{el.element_type} ({el.tag})</small>
                          </td>
                          <td className="py-4">
                            <code className="has-background-black-ter has-text-success px-2 py-1 is-size-7">
                              {el.recommended_locator.value}
                            </code>
                          </td>
                          <td className="py-4">
                            <span className="tag is-dark is-family-monospace">{el.recommended_locator.strategy}</span>
                          </td>
                          <td className="py-4 pr-5 has-text-centered">
                            <span className={`has-text-weight-bold ${el.recommended_locator.score > 80 ? 'has-text-success' : 'has-text-warning'}`}>
                              {el.recommended_locator.score}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  
                  {results.elements.length === 0 && (
                     <div className="p-6 has-text-centered has-text-grey">
                        No interesting elements found in the provided HTML.
                     </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
