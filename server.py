import subprocess
import tempfile
import traceback

import markdown2
from flask import Flask, request, send_from_directory, send_file, Response, abort
import os

app = Flask(__name__)


@app.route('/mostrar-archivo/<filename>')
def mostrar_archivo(filename):
    """
    Devuelve un archivo al cliente para su descarga.
    :param filename: El nombre del archivo que se desea mostrar o descargar.
    :return None Un objeto de respuesta Flask que contiene el archivo solicitado.
    :raise 404 Not Found: Si el archivo no existe en la carpeta 'upload'.
    """
    # Ruta del archivo en la carpeta upload
    ruta_archivo = os.path.join("upload", filename)

    # Comprobar si existe
    if os.path.exists(ruta_archivo):
        # Utiliza send_file para enviar el archivo al cliente con as_attachment
        return send_file(ruta_archivo, as_attachment=True)
    else:
        # Devuelve un código de estado 404 si el archivo no existe
        abort(404)


@app.route('/mi_pagina.html')
def mostrar_mi_pagina():
    """
    Muestra la pagina que se ha renderizado del direct

    :return: n objeto de respuesta Flask que contiene la página HTML.
    """
    # Ruta del archivo en la carpeta uploads
    ruta_archivo = 'upload/mi_pagina.html'

    # Utiliza send_file para enviar el archivo al cliente sin el as_attachment=True
    return send_file(ruta_archivo)


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Sube un archivo al servidor.

    :return: Un mensaje indicando que el archivo se ha subido con éxito.
    :raise 400 Bad Request: Si no se proporciona ningún archivo en la solicitud POST.
    :raise 500 Internal Server Error: Si ocurre un error al intentar guardar el archivo en el servidor.
    """
    file = request.files['file']
    file.save(os.path.join("upload", file.filename))
    return 'Archivo subido con éxito'


@app.route('/upload/<filename>', methods=['GET'])
def download_file(filename):
    """
    Descarga un archivo del servidor.

    :param filename: El nombre del archivo que se desea descargar.
    :return: n objeto de respuesta Flask que contiene el archivo solicitado.
    :raise 404 Not Found: Si el archivo no existe en la carpeta 'upload'.
    """
    return send_from_directory('upload', filename)


@app.route('/markdown-to-html/<filename>', methods=['GET'])
def convert_to_html(filename):
    """
    Convierte un archivo Markdown a HTML y proporciona la descarga del resultado.

    :param filename: El nombre del archivo Markdown que se desea convertir.
    :return: Un objeto de respuesta Flask que contiene el archivo HTML generado.
    :raise 404 Not Found: Si el archivo Markdown no existe en la carpeta 'upload'.
    :raise 500 Internal Server Error: Si ocurre un error al procesar o guardar el archivo HTML.
    """
    filepath = os.path.join("upload", filename)

    if os.path.exists(filepath):
        # Leer el contenido del archivo Markdown
        with open(filepath, 'r', encoding='utf-8') as file:
            contenido_markdown = file.read()

        # Convertir Markdown a HTML
        contenido_html = markdown2.markdown(contenido_markdown)

        html_filepath = os.path.join("upload", f'{filename}.html')

        # Guardar el contenido HTML en un archivo
        with open(html_filepath, 'w', encoding='utf-8') as html_file:
            html_file.write(contenido_html)

        # Enviar el archivo HTML para su descarga
        return send_file(html_filepath, as_attachment=True)
    else:
        return f'Error: El archivo {filename} no existe'


@app.route('/markdown-to-html-direct/<filename>', methods=['GET'])
def convert_to_html_direct(filename):
    """
    Convierte un archivo Markdown a HTML y devuelve el contenido HTML directamente.

    :param filename: El nombre del archivo Markdown que se desea convertir.
    :return: El contenido HTML generado como una respuesta directa.
    :raise 404 Not Found: Si el archivo Markdown no existe en la carpeta 'upload'.
    :raise 500 Internal Server Error: Si ocurre un error al procesar o convertir el archivo Markdown.
    """
    filepath = os.path.join("upload", filename)

    if os.path.exists(filepath):
        # Leer el contenido del archivo Markdown
        with open(filepath, 'r', encoding='utf-8') as file:
            contenido_markdown = file.read()

        # Convertir Markdown a HTML
        contenido_html = markdown2.markdown(contenido_markdown)

        # Enviar el archivo HTML para su descarga
        return contenido_html
    else:
        return f'Error: El archivo {filename} no existe'


@app.route('/markdown-to-pdf/<filename>', methods=['GET'])
def convert_to_pdf(filename):
    """
    Convierte un archivo Markdown a PDF y proporciona la descarga del resultado.

    :param filename: El nombre del archivo Markdown que se desea convertir.
    :return: Un objeto de respuesta Flask que contiene el archivo PDF generado.
    :raise 404 Not Found: Si el archivo Markdown no existe en la carpeta 'upload'.
    :raise 500 Internal Server Error: Si ocurre un error al procesar o convertir el archivo Markdown a PDF.
    """
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
            archivo_pdf = os.path.join("upload", f'{filename.replace(".md", ".pdf")}')
            pandoc(temp.name, archivo_pdf)

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


def pandoc(input_file, output_file):
    """
    Convierte un archivo Markdown a PDF utilizando Pandoc.

    :param input_file: Ruta del archivo de entrada en formato Markdown.
    :param output_file: Ruta del archivo de salida en formato PDF.
    :return: None
    :raise Exception: Si ocurre un error durante la conversión, se eleva una excepción con detalles del error.
    """
    try:
        subprocess.run(["pandoc", input_file, "-o", output_file])
    except Exception as e:
        raise Exception(f"Error al convertir Markdown a PDF usando Pandoc. Detalles del error:\n{e}")


if __name__ == '__main__':
    app.run(port=8000)
