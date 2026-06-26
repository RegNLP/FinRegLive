# Step 05 - Processing Package
#
# Role:
#   Mark the processing folder as a Python package.
#
# Why this exists:
#   Processing modules such as cleaning, chunking, and metadata helpers need to
#   be importable by ingestion, retrieval, and indexing code.
#
# Input:
#   None.
#
# Output:
#   A package namespace named backend.processing.
