CodeKG — Command Workflow
	•	codekg build-sqlite --repo ~/repos/personal_agent/src --db ~/repos/personal_agent/codekg.sqlite --wipe
Build the authoritative SQLite knowledge graph from the Python source tree using AST analysis.
	•	codekg build-lancedb --sqlite ~/repos/personal_agent/codekg.sqlite --wipe
Create a semantic vector index (LanceDB) over graph nodes for natural-language retrieval.
	•	codekg query "database connection url configuration" --sqlite ~/repos/personal_agent/codekg.sqlite --top 8
Run a hybrid semantic + graph query to retrieve structurally related code elements.
	•	codekg pack "database connection url configuration" --sqlite ~/repos/personal_agent/codekg.sqlite --top 8
Execute the query and emit a ranked, deduplicated, source-grounded snippet pack in Markdown.
	•	open /tmp/codekg_pack.md
Review the extracted definitions and call-site snippets with full source provenance.
