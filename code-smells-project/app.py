import logging

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

import config
from routes.admin_routes import admin_bp
from routes.health_routes import health_bp
from routes.pedidos_routes import pedidos_bp
from routes.produtos_routes import produtos_bp
from routes.relatorios_routes import relatorios_bp
from routes.usuarios_routes import usuarios_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["DEBUG"] = config.DEBUG
CORS(app)

app.register_blueprint(produtos_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(pedidos_bp)
app.register_blueprint(relatorios_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(health_bp)


@app.errorhandler(HTTPException)
def handle_http_error(e):
    return jsonify({"erro": e.description}), e.code


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    logger.exception("Erro não tratado")
    return jsonify({"erro": "Erro interno"}), 500


@app.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", config.HOST, config.PORT)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
