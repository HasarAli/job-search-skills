"""Company check: can a company employ the user where they live?

* ``settings`` — the ``company_check:`` block of ``config.yaml``.
* ``evidence`` — turns locations, posting text and job-board rows into evidence.
* ``boards`` — recognises job-board links, reads boards, and finds a company's board.
* ``check`` — records evidence and labels postings during a run, and backs the CLI.
* ``tenants`` — keeps ``config.yaml``'s board lists in step with the labels.

Labels and evidence rules live in ``search_shared.companies``; storage in the ledger.
"""
