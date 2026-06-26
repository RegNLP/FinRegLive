# Step 04 - Ingestion Package
#
# Role:
#   Mark the ingestion folder as a Python package.
#
# Why this exists:
#   Ingestion modules such as RSS, HTML, and deduplication helpers need to be
#   importable by the backend and later pipeline code.
#
# Input:
#   None.
#
# Output:
#   A package namespace named backend.ingestion.
