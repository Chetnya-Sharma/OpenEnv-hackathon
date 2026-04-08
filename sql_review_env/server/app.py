"""App entry point for openenv multi-mode deployment."""

import uvicorn
from .main import app


def main():
    """Start the environment server."""
    uvicorn.run(app, host="0.0.0.0", port=7860, workers=1)


if __name__ == "__main__":
    main()
