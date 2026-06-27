# Step 18D - Pipeline Package
#
# Role:
#   Orchestrate route-aware RAG flows.
#
# Why this exists:
#   Routing, retrieval, reranking, diagnostics, and generation should be joined
#   in one pipeline layer instead of being scattered across API handlers.
#
# Input:
#   User questions.
#
# Output:
#   Structured route-aware answer results.
