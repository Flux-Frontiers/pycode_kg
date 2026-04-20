PyCodeKG — Command Workflow
	•	pycodekg build-sqlite --repo ~/repos/personal_agent/src --db ~/repos/personal_agent/pycodekg.sqlite --wipe
Build the authoritative SQLite knowledge graph from the Python source tree using AST analysis.
	•	pycodekg build-lancedb --sqlite ~/repos/personal_agent/pycodekg.sqlite --wipe
Create a semantic vector index (LanceDB) over graph nodes for natural-language retrieval.
	•	pycodekg query "database connection url configuration" --sqlite ~/repos/personal_agent/pycodekg.sqlite --top 8
Run a hybrid semantic + graph query to retrieve structurally related code elements.
	•	pycodekg pack "database connection url configuration" --sqlite ~/repos/personal_agent/pycodekg.sqlite --top 8
Execute the query and emit a ranked, deduplicated, source-grounded snippet pack in Markdown.
	•	open /tmp/pycodekg_pack.md
Review the extracted definitions and call-site snippets with full source provenance.
