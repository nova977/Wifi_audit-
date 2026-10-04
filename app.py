from flask import Flask
import routes
import logging
import sys
app = Flask(__name__)

routes.register(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
