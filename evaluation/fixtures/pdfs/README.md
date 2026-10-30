# Official PDF fixtures

Drop recruitment-notification PDFs downloaded manually from an allowed official source into one subfolder per notice:

```text
pdfs/<notice-id>/<advertisement>.pdf
pdfs/<notice-id>/expected.json
```

Download the PDFs manually; do not crawl. Read each PDF directly and hand-write `expected.json`; do not generate labels by running the extractor. Record the official URL, download date, and SHA-256 in `manifest.json` only after the PDF has actually been downloaded.

The current labeled sample size is **N=3** official MPPSC recruitment notifications:
1. `advt_ad_farmers_welfare_2026`: Assistant Director, Farmers Welfare & Agriculture Development (Statistics) Exam 2026 (Advt 09/2026)
2. `advt_assistant_director_2026`: Assistant Director (Higher Education Department) Exam 2026 (Advt 12/2026)
3. `advt_law_officer_2026`: Law Officer (Jail Department) Exam 2026 (Advt 13/2026)

Exam rulebooks (separate document type) are stored in `../rulebooks/`.

CI never contacts Anthropic. If a fixture needs LLM extraction, record the JSON response in `../model_responses.json`, keyed by the SHA-256 of the exact page-and-table text sent to the extractor. An empty map means CI uses the deterministic fallback.
