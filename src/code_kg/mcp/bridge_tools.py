"""
MCP tool hooks for bridge centrality in CodeKG.
"""

# Placeholder for MCP integration


def top_bridges(kind="module", limit=20):
    from code_kg.analysis.bridge import compute_bridge_centrality

    bridges = compute_bridge_centrality(kind=kind, top=limit)
    return bridges


def why_bridge(node_id):
    # TODO: Explain why a node is a bridge
    pass
