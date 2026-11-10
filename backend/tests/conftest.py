import os

# Use a throwaway in-memory database for every test run.
os.environ["DATABASE_URL"] = "sqlite://"
