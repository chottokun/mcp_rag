import uvicorn
from .factory import create_app
import os

# Create the app instance using the factory
# It will automatically pick up the API_KEY from the environment
app = create_app()

# This allows running the app with `python -m app.main`
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
