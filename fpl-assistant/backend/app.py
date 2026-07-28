from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    db.init_app(app)

    from routes.auth import auth_bp
    from routes.players import players_bp
    from routes.teams import teams_bp
    from routes.fixtures import fixtures_bp
    from routes.squads import squads_bp
    from routes.watchlist import watchlist_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(players_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(fixtures_bp)
    app.register_blueprint(squads_bp)
    app.register_blueprint(watchlist_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
