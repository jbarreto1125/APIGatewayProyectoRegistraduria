from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
import json
from waitress import serve
from flask_jwt_extended import create_access_token, verify_jwt_in_request
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
import requests
import datetime
import re

app = Flask(__name__)
cors = CORS(app)
app.config["JWT_SECRET_KEY"] = "proyectoregistraduria"
jwt = JWTManager(app)


def load_file_config():
    with open("config.json") as f:
        return json.load(f)


@app.before_request
def before_request_callback():
    url = limpiar_url(request.path)
    excluded_routes = ["/login"]
    if url in excluded_routes:
        print("Ruta excluida del middleware", url)
    else:
        if verify_jwt_in_request():
            usuario = get_jwt_identity()
            rol = usuario["rol"]
            if rol is not None:
                if not validar_permiso(url, request.method.upper(), rol["_id"]):
                    return jsonify({"message": "Permission denied"}), 401
            else:
                return jsonify({"message": "Permission denied"}), 401
        else:
            return jsonify({"message": "Permission denied"}), 401


def limpiar_url(url):
    partes = url.split("/")

    for p in partes:
        if re.search("\\d", p):
            url = url.replace(p, "?")

    return url


def validar_permiso(url, metodo, id_rol):
    config_data = load_file_config()
    url_seguridad = config_data["url-backend-security"] + "/permiso_rol/validar-permiso/rol/" + id_rol
    headers = {"Content-Type": "application/json; charset=utf-8"}
    body = {
        "url": url,
        "metodo": metodo
    }

    response = requests.post(url_seguridad, headers=headers, json=body)
    return response.status_code == 200


@app.route("/login", methods=["POST"])
def create_token():
    data = request.get_json()
    config_data = load_file_config()
    url = config_data["url-backend-security"] + "/usuarios/validate"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        user = response.json()
        expires = datetime.timedelta(seconds=60 * 60 * 24)
        token = create_access_token(identity=user, expires_delta=expires)
        return jsonify({"token": token, "user_id": user["_id"]})
    else:
        return jsonify({"message": "Usuario o Contraseña incorrectas"}), 401


@app.route("/candidatos", methods=["GET"])
def listar_candidatos():
    config_data = load_file_config()
    url = config_data["url-backend-academic"] + "/candidatos"
    response = requests.get(url)
    return jsonify(response.json())


if __name__ == "__main__":
    data_config = load_file_config()
    print(f"Server Running: http://{data_config['url-backend']}:{data_config['port']}")
    serve(app, host=data_config["url-backend"], port=data_config["port"])
