import os
import subprocess
import tempfile
import time
import traceback
import flet
import markdown
import requests
from flet import (
    ElevatedButton,
    FilePicker,
    FilePickerResultEvent,
    Page,
    Text,
    icons,
    Dropdown,
    FilePickerUploadFile
)

carpeta_temporal = tempfile.mkdtemp()


class App:
    def __init__(self, page):
        self.page = page
        self.file_picker = FilePicker()
        self.archivos = []

        self.file_picker.on_result = self.file_picker_result

        # hide dialog in a overlay
        self.page.overlay.append(self.file_picker)

        self.page.add(
            ElevatedButton(
                "Seleccionar archivo...",
                icon=icons.FOLDER_OPEN,
                on_click=lambda _: self.file_picker.pick_files(allow_multiple=False),
            ),
        )

        # Añadir dropdown
        self.dropdown = Dropdown(
            width=100,
            options=[
                flet.dropdown.Option("pdf"),
                flet.dropdown.Option("html"),
            ],
        )
        self.page.add(self.dropdown)

        # Añadir botón submit
        self.page.add(ElevatedButton(text="Submit", on_click=self.submit_clicked))

    def file_picker_result(self, e: FilePickerResultEvent):
        if e.files is not None:
            for f in e.files:
                self.archivos.append(f.name)
                # Subir el archivo al servidor
                upload_url = self.page.get_upload_url(f.name, 60)
                upload_file = FilePickerUploadFile(f.name, upload_url)
                self.file_picker.upload([upload_file])
                print(carpeta_temporal)
                archivo_en_carpeta = os.path.join(carpeta_temporal, f.name)
                print(r"Ruta del archivo:", archivo_en_carpeta)
                time.sleep(1)
                with open(archivo_en_carpeta, 'rb') as file:
                    requests.post("http://localhost:8000/upload", files={'file': file})
                # Enviar una solicitud al servidor para obtener el contenido del archivo
                response = requests.get(f'http://localhost:8000/upload/{f.name}')
                print(response.text)
                self.page.add(Text(f"Nombre del archivo seleccionado: {f.name}"))
        self.page.update()

    def submit_clicked(self, e):
        if self.dropdown.value == "html":
            self.convert_md_to_html()
        elif self.dropdown.value == "pdf":
            self.convert_md_to_pdf()

    def convert_md_to_html(self):
        # Crear la carpeta 'downloads' si no existe
        carpeta_descargas = 'downloads'
        os.makedirs(carpeta_descargas, exist_ok=True)

        for archivo in self.archivos:
            # Obtener el contenido del archivo Markdown desde el servidor
            response = requests.get(f'http://localhost:8000/upload/{archivo}')

            if response.status_code == 200:
                # Convertir el contenido de Markdown a HTML
                contenido_markdown = response.text
                contenido_html = markdown.markdown(contenido_markdown)

                # Guardar el contenido HTML en un archivo en la carpeta 'downloads'
                archivo_html = os.path.join(carpeta_descargas, f'{archivo.replace(".md", ".html")}')
                with open(archivo_html, 'w', encoding='utf-8') as archivo_salida:
                    archivo_salida.write(contenido_html)

                print(f"Contenido HTML para {archivo} guardado en {archivo_html}")
            else:
                print(f"Error al obtener el archivo {archivo}. Estado de la respuesta: {response.status_code}")

    def convert_md_to_pdf(self):
        for archivo in self.archivos:
            # Obtener el contenido del archivo Markdown desde el servidor
            url_archivo = f'http://localhost:8000/upload/{archivo}'
            response = requests.get(url_archivo)

            if response.status_code == 200:
                # Crea un archivo temporal
                temp = tempfile.NamedTemporaryFile(delete=False)

                try:
                    # Escribe el contenido de Markdown en el archivo temporal
                    with open(temp.name, 'w', encoding='utf-8') as f:
                        f.write(response.text)

                    # Convertir el archivo de Markdown a PDF usando Pandoc
                    archivo_pdf = os.path.join("downloads", f'{archivo.replace(".md", ".pdf")}')
                    self.convert_md_to_pdf_with_pandoc(temp.name, archivo_pdf)
                    print(f"Contenido PDF para {archivo} guardado en {archivo_pdf}")
                except Exception as e:
                    traceback.print_exc()
                    print(f"Error al convertir {archivo} a PDF. Detalles del error:\n{e}")
                finally:
                    # Cierra el archivo temporal antes de intentar eliminarlo
                    temp.close()
                    # Elimina el archivo temporal
                    os.unlink(temp.name)
            else:
                traceback.print_exc()
                print(
                    f"Error al obtener el archivo {archivo} desde {url_archivo}. Estado de la respuesta: {response.status_code}")

    def convert_md_to_pdf_with_pandoc(self, input_file, output_file):
        try:
            subprocess.run(["pandoc", input_file, "-o", output_file])
        except Exception as e:
            raise Exception(f"Error al convertir Markdown a PDF usando Pandoc. Detalles del error:\n{e}")


def main(page: Page):
    app = App(page)


flet.app(target=main, view=flet.WEB_BROWSER, upload_dir=carpeta_temporal)
