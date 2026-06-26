# Step 03 - Database Package
#
# Role:
#   Mark the database folder as a Python package.
#
# Why this exists:
#   Database modules such as backend.database.db and backend.database.models
#   need to be importable by the FastAPI app and later pipeline code.
#
# Input:
#   None.
#
# Output:
#   A package namespace named backend.database.
