"""
MCP tool hooks for framework node detection in CodeKG.
"""

# Placeholder for MCP integration


def detect_framework_nodes(limit=20):
    from code_kg.analysis.framework_detector import (
        detect_framework_nodes as detect_fw,
    )

    return detect_fw(limit=limit)


def why_framework_node(node_id):
    # TODO: Explain why a node is a framework node
    pass
