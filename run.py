from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    debug_ativo = os.environ.get("DEBUG", "false").lower() == "true"

    app.run(debug=debug_ativo)