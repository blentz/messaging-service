"""
Main application entry point for the unified messaging service.
"""

import os

from app import create_app

# Create Flask application
app = create_app()

def main():
    """Main function to start the development server."""
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)

if __name__ == "__main__":
    # Development server
    main()
