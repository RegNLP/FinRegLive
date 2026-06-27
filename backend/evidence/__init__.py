# Step 18C - Evidence Package
#
# Role:
#   Inspect retrieved evidence before answer generation.
#
# Why this exists:
#   Route-aware RAG needs more than retrieved chunks. It needs diagnostics that
#   explain whether evidence is strong, diverse, risky, or too weak to answer.
#
# Input:
#   Retrieved evidence chunks and route policy.
#
# Output:
#   Evidence diagnostics used by later routing, verification, and fallback steps.
