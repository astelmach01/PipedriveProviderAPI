import os
from website import create_app

app = create_app()

if __name__ == "__main__":
    port = os.getenv("PORT", 5000)
    app.run(debug=True, port=port)
