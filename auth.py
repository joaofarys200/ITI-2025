from flask import Flask, request, jsonify, send_file,render_template,url_for,redirect, Response
import os
import socket
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

#observacoes feitas,apenas funciona por causa do html,sem ele nao consigo redirecionar os url,logo tenho que testar no postman a api.
app = Flask(__name__)

# Dentro do container, a pasta partilhada é montada em /app/storage (ver docker-compose.yml)
BASE_DIR = "/app/storage"
app.config["BASE_DIR"] = BASE_DIR
#coisas para o prometheus
REQUEST_COUNT = Counter("app_requests_total", "Total de pedidos HTTP", ["endpoint", "hostname"])

@app.before_request
def before_request():
    REQUEST_COUNT.labels(request.path, socket.gethostname()).inc()


@app.route("/")
def home():
    print(f"Home handled by {socket.gethostname()}")
    files=os.listdir(BASE_DIR)
    return render_template("index.html", files=files)

@app.route("/upload", methods=["POST"])
def upload_file():
    print(f"Upload handled by {socket.gethostname()}")
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    file_path = os.path.join(app.config["BASE_DIR"], file.filename)
    file.save(file_path)
    return redirect(url_for('home'))

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_file(os.path.join(app.config["BASE_DIR"], filename))

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(app.config['BASE_DIR'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('home'))


socket.gethostname()


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

#add to git