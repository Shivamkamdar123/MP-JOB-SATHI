# Official PDF fixtures

Drop 5-10 recent recruitment-notification PDFs downloaded manually from an allowed official source into one subfolder per notice:

```text
pdfs/<notice-id>/notification.pdf
pdfs/<notice-id>/expected.json
```

Download the PDFs manually; do not crawl. Read each PDF directly and hand-write `expected.json`; do not generate labels by running the extractor. Record the official URL, download date, and SHA-256 in `manifest.json` only after the PDF has actually been downloaded. The current labeled sample size is N=0; no accuracy target is claimed.

CI never contacts Anthropic. If a fixture needs LLM extraction, record the JSON response in `../model_responses.json`, keyed by the SHA-256 of the exact page-and-table text sent to the extractor. An empty map means CI uses the deterministic fallback.