"""Run the Flask app without the debug reloader."""

from app import create_app


if __name__ == "__main__":
    create_app().run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True,
    )
