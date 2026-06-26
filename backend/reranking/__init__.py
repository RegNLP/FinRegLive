# Step 16 - Reranking Package
#
# Role:
#   Provide reranking helpers used after first-pass retrieval.
#
# Why this exists:
#   Retrieval may return useful candidates mixed with weak matches. Reranking
#   gives the system a dedicated place to reorder evidence before generation.
#
# Input:
#   Retrieved evidence candidates.
#
# Output:
#   Reordered evidence candidates.
