"""
MCP tool hooks for bridge centrality in PyCodeKG.
"""

# Placeholder for MCP integration


def top_bridges(kind="module", limit=20):
    from pycode_kg.analysis.bridge import compute_bridge_centrality

    bridges = compute_bridge_centrality(kind=kind, top=limit)
    return bridges


def why_bridge(node_id):
    # TODO: Explain why a node is a bridge
    pass
