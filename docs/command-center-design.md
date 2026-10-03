# AIbrief command center

The approved reference is implemented as a static page served from `web/`.
The existing pipeline renders `web/landing-template.html` to both `index.html`
and `brief.html`; no React build or deployment migration is required.

The header provides region and topic filters, search and English/Arabic controls.
Selecting a record opens its event, evidence, impact, action and confidence in
the desktop inspector or a native modal dialog on smaller screens.

All views share a URL-deduplicated union of the main briefing and X feed.
Latest Signals counts unique records in this snapshot, not records published today.
It states its displayed count and matching total. Its X filter keeps
single-source posts visible. Saudi Intelligence searches Arabic and English text
across both feeds.

Evidence labels use `web/evidence-policy.js` and the existing server policy.
Single-source and collector-supplied verification claims remain unverified.
Corroborated requires reviewed independent support; verified also requires a
primary source. Act Now requires verified support, a score of at least 70 and
an event within 48 hours. Links without review remain links, not confirmed evidence.
Unknown impact is labeled as unassessed. No invented news, metrics or evidence
from the design reference is published.

The page follows the approved screenshot's sections without additional feeds.
The Miami photograph is generated illustration, not evidence for a story.
Original article and post links remain available in the details panel.
Saved links stay on the reader's device; sharing copies the original URL.

Checks: `node --test tests/test_command_center.cjs`, evidence-policy unit tests,
YAML parsing and desktop/mobile browser interaction checks. Rollback: restore
the previous landing template, index and brief from the preceding commit.
