# TWIST Automation Studio — Published Site

This folder contains the automation storefront and supporting workflow data published at:

https://twist5202-ux.github.io/automation/

## Organization

- `index.html` — public automation landing page
- `cs/`, `demo/`, `harga/` — related public pages
- Workflow-category directories — JSON exports for n8n use cases
- `automation/` — an additional nested collection; do not assume its files are identical to the files one level above
- `README-ID.md` — Indonesian documentation

## Editing safely

This folder is part of the live `twist5202-ux.github.io` repository. Keep the current directory paths, `index.html`, JavaScript, CSS, and navigation URLs intact until changes are browser-tested. Duplicate-looking templates may represent distinct revisions. Before importing any n8n JSON workflow, inspect and configure its credentials, webhooks, and service endpoints.

The separate [twist-automation repository](https://github.com/twist5202-ux/twist-automation) contains another working copy of the automation project. Changes between the two are **not automatically synchronized** just because their folder names match.

Security research write-ups are documented in [security-writeups](https://github.com/twist5202-ux/security-writeups).
