from flask import Flask, request, jsonify, send_file,render_template,url_for,redirect, Response, abort, g
import os
import shutil
import socket
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

#observacoes feitas,apenas funciona por causa do html,sem ele nao consigo redirecionar os url,logo tenho que testar no postman a api.
app = Flask(__name__)

# Dentro do container, a pasta partilhada é montada em /app/storage (ver docker-compose.yml)
BASE_DIR = "/app/storage"
app.config["BASE_DIR"] = BASE_DIR
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB
#coisas para o prometheus
REQUEST_COUNT = Counter("app_requests_total", "Total de pedidos HTTP", ["endpoint", "hostname"])
REQUEST_LATENCY = Histogram("app_request_duration_seconds", "Latencia de pedidos em segundos", ["endpoint"])
REQUEST_STATUS = Counter("app_requests_status_total", "Total de pedidos HTTP por status", ["endpoint", "status"])
IN_PROGRESS = Gauge("app_inprogress_requests", "Pedidos em progresso", ["hostname"])

FORBIDDEN_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".sh",
    ".ps1",
    ".php",
    ".js",
    ".jar",
    ".dll",
    ".so",
    ".py",
}


def _safe_name(name: str) -> str | None:
    if not name:
        return None
    if "/" in name or "\\" in name:
        return None
    normalized = os.path.normpath(name)
    if normalized.startswith(".."):
        return None
    return normalized

@app.before_request
def before_request():
    g.start_time = time.time()
    hostname = socket.gethostname()
    REQUEST_COUNT.labels(request.path, hostname).inc()
    IN_PROGRESS.labels(hostname).inc()


@app.after_request
def after_request(response):
    hostname = socket.gethostname()
    duration = time.time() - getattr(g, "start_time", time.time())
    REQUEST_LATENCY.labels(request.path).observe(duration)
    REQUEST_STATUS.labels(request.path, str(response.status_code)).inc()
    return response


@app.teardown_request
def teardown_request(exc):
    hostname = socket.gethostname()
    IN_PROGRESS.labels(hostname).dec()


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
    safe_name = _safe_name(file.filename)
    if not safe_name:
        return "Invalid filename", 400
    _, ext = os.path.splitext(safe_name)
    if ext.lower() in FORBIDDEN_EXTENSIONS:
        return "Executable or script files are not allowed", 400
    file_path = os.path.join(app.config["BASE_DIR"], safe_name)
    file.save(file_path)
    return redirect(url_for('home'))

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    safe_name = _safe_name(filename)
    if not safe_name:
        abort(400)
    file_path = os.path.join(app.config["BASE_DIR"], safe_name)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(file_path)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    safe_name = _safe_name(filename)
    if not safe_name:
        abort(400)
    file_path = os.path.join(app.config['BASE_DIR'], safe_name)
    if os.path.exists(file_path):
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
    return redirect(url_for('home'))


@app.route('/update/<filename>', methods=['POST'])
def update_file(filename):
    safe_old = _safe_name(filename)
    if not safe_old:
        abort(400)
    new_name = request.form.get('new_name')
    if not new_name:
        return "No new name provided", 400
    safe_new = _safe_name(new_name)
    if not safe_new:
        return "Invalid new name", 400

    old_path = os.path.join(app.config["BASE_DIR"], safe_old)
    new_path = os.path.join(app.config["BASE_DIR"], safe_new)

    if not os.path.exists(old_path):
        return "Original file not found", 404

    os.rename(old_path, new_path)
    return redirect(url_for('home'))


socket.gethostname()


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False)

#add to git