import { useEffect, useState } from 'react'
import { api } from './api';

function App() {
  const [url, setUrl] = useState('https://github.com/login')
  const [goal, setGoal] = useState('Find Username, Password, and Sign In button')

  // State for Interactive Mode
  const [browserOpen, setBrowserOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('gpt-4o') // Changed to a common OpenAI model for consistency
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  // Column Visibility (Added Selenium & Cypress)
  const [visibleColumns, setVisibleColumns] = useState({
    playwright: true,
    selenium: true,
    cypress: true,
    css: false,
    xpath: false
  })

  useEffect(() => {
    const storedKey = localStorage.getItem('ai_api_key')
    const storedModel = localStorage.getItem('ai_model')
    if (storedKey) setApiKey(storedKey)
    if (storedModel) setModel(storedModel)

    // No direct URL change listener like Electron IPC, relying on API responses for now.
    // Frontend could poll for current URL from backend if real-time updates are critical.
  }, [])

  const saveSettings = () => {
    localStorage.setItem('ai_api_key', apiKey)
    localStorage.setItem('ai_model', model)
    setIsSettingsOpen(false)
  }

  // STEP 1: Open Browser
  const handleOpenBrowser = async () => {
    try {
      const response = await api.openBrowser(url)
      setBrowserOpen(true)
      // If the backend returns the current URL after navigation, update it.
      if (response.url) {
        setUrl(response.url);
      }
    } catch (err: any) {
      console.error(err)
      alert('Failed to open browser: ' + err.message)
    }
  }

  // STEP 2: Scan Page
  const handleScan = async () => {
    setLoading(true)
    setResults(null)
    try {
      const data = await api.scanPage(goal, apiKey, model)
      setResults(data)
    } catch (err: any) {
      console.error(err)
      setResults({ error: 'Scan failed: ' + err.message })
    } finally {
      setLoading(false)
    }
  }

  const handleCloseBrowser = async () => {
    try {
      await api.closeBrowser()
      setBrowserOpen(false) // Update UI state
    } catch (err: any) {
      console.error(err)
      alert('Failed to close browser: ' + err.message)
    }
  }

  const handleHighlightElement = async (selector: string) => {
    try {
      await api.highlightElement(selector);
    } catch (err: any) {
      console.error(err);
      alert('Failed to highlight element: ' + err.message);
    }
  }

  const toggleColumn = (col: keyof typeof visibleColumns) => {
    setVisibleColumns((prev) => ({ ...prev, [col]: !prev[col] }))
  }

  return (
    <div className="container is-fluid" style={{ minHeight: '100vh' }}>
      {/* HEADER WITH SETTINGS BUTTON */}
      <div className="level my-5">
        <div className="level-left"></div>
        <div className="level-item has-text-centered">
          <span className="has-text-info is-size-4 has-text-weight-bold">🤖 Smart AI Locator</span>
        </div>
        <div className="level-right">
          <button
            className="button is-ghost has-text-grey-light"
            onClick={() => setIsSettingsOpen(true)}
            title="Configure API Key"
          >
            <span className="icon is-medium">⚙️</span>
          </button>
        </div>
      </div>

      {/* SETTINGS MODAL */}
      <div className={`modal ${isSettingsOpen ? 'is-active' : ''}`}>
        <div className="modal-background" onClick={() => setIsSettingsOpen(false)}></div>
        <div className="modal-card">
          <header className="modal-card-head has-background-dark">
            <p className="modal-card-title has-text-light">⚙️ AI Configuration</p>
            <button
              className="delete"
              aria-label="close"
              onClick={() => setIsSettingsOpen(false)}
            ></button>
          </header>
          <section className="modal-card-body has-background-dark-ter">
            <div className="field">
              <label className="label has-text-grey-light">OpenAI API Key</label> {/* Changed label */}
              <div className="control has-icons-left">
                <input
                  className="input is-dark"
                  type="password"
                  placeholder="sk-..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <span className="icon is-small is-left">🔑</span>
              </div>
            </div>

            <div className="field">
              <label className="label has-text-grey-light">AI Model</label>
              <div className="control">
                <div className="select is-fullwidth is-dark">
                  <select value={model} onChange={(e) => setModel(e.target.value)}>
                    <option value="gpt-4o">GPT-4o (Default)</option> {/* Changed options */}
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  </select>
                </div>
              </div>
            </div>
          </section>
          <footer
            className="modal-card-foot has-background-dark"
            style={{ justifyContent: 'flex-end' }}
          >
            <button className="button is-success" onClick={saveSettings}>
              Save Configuration
            </button>
          </footer>
        </div>
      </div>

      <section className="section pt-0">
        <div className="container">
          {/* CONTROL CARD */}
          <div className="card mb-6 has-background-dark-ter">
            <div className="card-content">
              {/* URL Input */}
              <div className="field">
                <label className="label has-text-grey-light is-size-7">Target URL</label>
                <div className="control">
                  <input
                    className="input is-dark is-family-monospace"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com"
                  />
                </div>
              </div>

              {/* Goal Input */}
              <div className="field">
                <label className="label has-text-grey-light is-size-7">Extraction Goal</label>
                <div className="control">
                  <textarea
                    className="textarea is-dark"
                    rows={2}
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    placeholder="e.g. Find the login button and user input"
                  />
                </div>
              </div>

              {/* ACTION AREA */}
              <div className="level mt-5">
                <div className="level-left">
                  {/* Status Indicator */}
                  {!browserOpen ? (
                    <div className="tags has-addons">
                      <span className="tag is-dark">Status</span>
                      <span className="tag is-warning">Ready to Launch</span>
                    </div>
                  ) : (
                    <div className="tags has-addons">
                      <span className="tag is-dark">Status</span>
                      <span className="tag is-success">Browser Connected</span>
                    </div>
                  )}
                </div>

                <div className="level-right">
                  <div className="buttons">
                    <button
                      className="button is-dark has-text-weight-bold"
                      onClick={handleOpenBrowser}
                      disabled={browserOpen} // Disable if already open to prevent dupes
                    >
                      <span>🌐 1. Open Browser</span>
                    </button>

                    {browserOpen && (
                      <button
                        className="button is-danger is-light has-text-weight-bold"
                        onClick={handleCloseBrowser}
                      >
                        <span>✖ Close</span>
                      </button>
                    )}
                    <button
                      className={`button is-info has-text-weight-bold ${loading ? 'is-loading' : ''}`}
                      onClick={handleScan}
                      disabled={!browserOpen || loading}
                    >
                      <span>📸 2. Scan Page</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* RESULTS SECTION */}
          {results && (
            <>
              <div className="level mb-4">
                <div className="level-left">
                  <h2 className="title is-5 has-text-light mb-0">
                    📊 Final Report{' '}
                    {Array.isArray(results) && (
                      <span className="has-text-grey is-size-6 has-text-weight-normal">
                        ({results.length} locators found)
                      </span>
                    )}
                  </h2>
                </div>

                {/* Column Toggles */}
                <div className="level-right">
                  <div className="field is-grouped is-grouped-multiline">
                    <div className="control">
                      <label className="checkbox has-text-grey-light mr-3 is-size-7">
                        <input
                          type="checkbox"
                          className="mr-1"
                          checked={visibleColumns.playwright}
                          onChange={() => toggleColumn('playwright')}
                        />
                        Playwright
                      </label>
                    </div>
                    <div className="control">
                      <label className="checkbox has-text-grey-light mr-3 is-size-7">
                        <input
                          type="checkbox"
                          className="mr-1"
                          checked={visibleColumns.selenium}
                          onChange={() => toggleColumn('selenium')}
                        />
                        Selenium
                      </label>
                    </div>
                    <div className="control">
                      <label className="checkbox has-text-grey-light mr-3 is-size-7">
                        <input
                          type="checkbox"
                          className="mr-1"
                          checked={visibleColumns.cypress}
                          onChange={() => toggleColumn('cypress')}
                        />
                        Cypress
                      </label>
                    </div>
                    <div className="control">
                      <label className="checkbox has-text-grey-light mr-3 is-size-7">
                        <input
                          type="checkbox"
                          className="mr-1"
                          checked={visibleColumns.css}
                          onChange={() => toggleColumn('css')}
                        />
                        CSS
                      </label>
                    </div>
                  </div>
                </div>
              </div>

              {/* Error Message */}
              {results.error && (
                <article className="message is-danger">
                  <div className="message-body">Error: {results.error}</div>
                </article>
              )}

              {/* Data Table */}
              {Array.isArray(results) && (
                <div
                  className="table-container box has-background-grey-darker p-0"
                  style={{ border: '1px solid #363636' }}
                >
                  <table className="table is-fullwidth is-hoverable is-striped has-background-dark has-text-light">
                    <thead>
                      <tr>
                        <th className="has-text-grey-light">Status</th>
                        <th className="has-text-grey-light">Element</th>

                        {visibleColumns.playwright && (
                          <th className="has-text-grey-light">Playwright</th>
                        )}
                        {visibleColumns.selenium && (
                          <th className="has-text-grey-light">Selenium</th>
                        )}
                        {visibleColumns.cypress && <th className="has-text-grey-light">Cypress</th>}
                        {visibleColumns.css && <th className="has-text-grey-light">CSS</th>}

                        <th className="has-text-grey-light">Reasoning</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map((item: any, idx: number) => (
                        <tr key={idx}>
                          <td style={{ verticalAlign: 'middle' }}>
                            <button
                              className={`tag is-small has-text-weight-bold ${
                                item.status === 'VERIFIED'
                                  ? 'is-success'
                                  : item.status === 'AMBIGUOUS'
                                    ? 'is-warning'
                                    : 'is-danger'
                              }`}
                              title="Highlight in Browser"
                              onClick={() => handleHighlightElement(item.cssSelector)}
                            >
                              <span> {item.status}</span>
                            </button>
                          </td>

                          <td
                            className="has-text-weight-semibold"
                            style={{ verticalAlign: 'middle' }}
                          >
                            {item.elementName}
                          </td>

                          {/* Playwright */}
                          {visibleColumns.playwright && (
                            <td style={{ verticalAlign: 'middle' }}>
                              <code
                                className="has-background-black-ter has-text-success px-2 py-1 is-size-7"
                                style={{ wordBreak: 'break-all' }}
                              >
                                {item.playwrightLocator}
                              </code>
                            </td>
                          )}

                          {/* Selenium */}
                          {visibleColumns.selenium && (
                            <td style={{ verticalAlign: 'middle' }}>
                              <code
                                className="has-background-black-ter has-text-warning px-2 py-1 is-size-7"
                                style={{ wordBreak: 'break-all' }}
                              >
                                {item.seleniumLocator}
                              </code>
                            </td>
                          )}

                          {/* Cypress */}
                          {visibleColumns.cypress && (
                            <td style={{ verticalAlign: 'middle' }}>
                              <code
                                className="has-background-black-ter has-text-info px-2 py-1 is-size-7"
                                style={{ wordBreak: 'break-all' }}
                              >
                                {item.cypressLocator}
                              </code>
                            </td>
                          )}

                          {/* CSS */}
                          {visibleColumns.css && (
                            <td style={{ verticalAlign: 'middle' }}>
                              <code
                                className="has-background-black-ter has-text-grey-lighter px-2 py-1 is-size-7"
                                style={{ wordBreak: 'break-all' }}
                              >
                                {item.cssSelector}
                              </code>
                            </td>
                          )}

                          <td
                            className="has-text-grey"
                            style={{
                              maxWidth: 200,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              verticalAlign: 'middle'
                            }}
                            title={item.reasoning}
                          >
                            {item.reasoning}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  )
}

export default App
