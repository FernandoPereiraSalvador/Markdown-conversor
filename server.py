from flask import Flask, request, send_from_directory
import os

app = Flask(__name__)


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file.save(os.path.join("upload", file.filename))
    return 'Archivo subido con éxito'


@app.route('/upload/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory('upload', filename)


if __name__ == '__main__':
    app.run(port=8000)
