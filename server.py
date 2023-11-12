import subprocess
import tempfile
import traceback

import markdown2
from flask import Flask, request, send_from_directory, send_file
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

@app.route('/markdown-to-html/<filename>', methods=['GET'])
def convert_to_html(filename):
    filepath = os.path.join("upload", filename)

    if os.path.exists(filepath):
        # Leer el contenido del archivo Markdown
        with open(filepath, 'r', encoding='utf-8') as file:
            contenido_markdown = file.read()

        # Convertir Markdown a HTML
        contenido_html = markdown2.markdown(contenido_markdown)

        # Guardar el contenido HTML en un archivo
        with open(f'{filename}.html', 'w', encoding='utf-8') as html_file:
            html_file.write(contenido_html)

        # Enviar el archivo HTML para su descarga
        return send_file(f'{filename}.html', as_attachment=True)
    else:
        return f'Error: El archivo {filename} no existe'

@app.route('/markdown-to-pdf/<filename>', methods=['GET'])
def convert_to_pdf(filename):
    filepath = os.path.join("upload", filename)
    print(filepath)

    if os.path.exists(filepath):
        # Leer el contenido del archivo Markdown
        with open(filepath, 'r', encoding='utf-8') as file:
            contenido_markdown = file.read()

        # Crea un archivo temporal
        temp = tempfile.NamedTemporaryFile(delete=False)

        try:
            # Escribe el contenido de Markdown en el archivo temporal
            with open(temp.name, 'w', encoding='utf-8') as f:
                f.write(contenido_markdown)

            # Convertir el archivo de Markdown a PDF usando Pandoc
            archivo_pdf = os.path.join("downloads", f'{filename.replace(".md", ".pdf")}')
            convert_md_to_pdf_with_pandoc(temp.name, archivo_pdf)
            print(f"Contenido PDF para {filename} guardado en {archivo_pdf}")

            # Enviar el archivo PDF para su descarga
            return send_file(archivo_pdf, as_attachment=True)
        except Exception as e:
            traceback.print_exc()
            print(f"Error al convertir {filename} a PDF. Detalles del error:\n{e}")
        finally:
            # Cierra el archivo temporal antes de intentar eliminarlo
            temp.close()
            # Elimina el archivo temporal
            os.unlink(temp.name)
    else:
        return f'Error: El archivo {filename} no existe'

def convert_md_to_pdf_with_pandoc(input_file, output_file):
    try:
        subprocess.run(["pandoc", input_file, "-o", output_file])
    except Exception as e:
        raise Exception(f"Error al convertir Markdown a PDF usando Pandoc. Detalles del error:\n{e}")

if __name__ == '__main__':
    app.run(port=8000)
