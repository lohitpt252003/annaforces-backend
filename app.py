from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# from api.users import users_bp
from api.problems_api import problems_bp
from api.submissions_api import submissions_bp
# from api.contests_api import contests_bp
# from api.admin import admin_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    # app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(problems_bp, url_prefix='/api/problems')
    app.register_blueprint(submissions_bp, url_prefix='/api/submissions')
    # app.register_blueprint(contests_bp, url_prefix='/api/contests')
    # app.register_blueprint(admin_bp, url_prefix='/api/admin')

    @app.route("/")
    def root():
        return {"message": "Backend is running 🎯"}
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)