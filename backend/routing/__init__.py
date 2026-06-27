# Step 18A - Routing Package
#
# Role:
#   Classify user questions and prepare route decisions for the RAG pipeline.
#
# Why this exists:
#   Not every question should use the same retrieval depth, reranking policy,
#   model cost, or verification level. Routing starts by understanding the
#   question type.
#
# Input:
#   User questions.
#
# Output:
#   Structured classification and route hints.
