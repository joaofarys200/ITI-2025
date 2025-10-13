from flask import Flask, request, jsonify, send_file,render_template,url_for,redirect
import os
#observacoes feitas,apenas funciona por causa do html,sem ele nao consigo redirecionar os url,logo tenho que testar no postman a api.
app = Flask(__name__)

BASE_DIR = "storage"
os.makedirs(BASE_DIR, exist_ok=True)
app.config["BASE_DIR"] = BASE_DIR

@app.route("/")
def home():
    files=os.listdir(BASE_DIR)
    return render_template("index.html", files=files)

@app.route("/upload", methods=["POST"])
def upload_file():
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

if __name__ == "__main__":
    app.run(debug=True)

#add to git