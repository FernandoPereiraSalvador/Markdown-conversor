import os
import re
import tempfile
import time
import flet as ft
import requests
from flet import (
    ElevatedButton,
    FilePicker,
    FilePickerResultEvent,
    Page,
    icons,
    Dropdown,
    FilePickerUploadFile,
)

carpeta_temporal = tempfile.mkdtemp()


class App:
    def __init__(self, page):
        self.page = page
        self.file_picker = FilePicker()
        self.archivos = []

        self.filter = ft.Tabs(
            scrollable=False,
            selected_index=0,
            on_change=self.tabs_changed,
            tabs=[ft.Tab(text="Upload files"), ft.Tab(text="Direct")],
        )

        self.page.add(self.filter)

        self.file_picker.on_result = self.file_picker_result

        self.page.overlay.append(self.file_picker)

        self.submit = ElevatedButton(text="Submit", on_click=self.submit_clicked,
                                     disabled=True)

        self.barra_progreso = ft.ProgressBar(width=250, color="blue", bgcolor="#eeeeee", visible=False)

        # Añadir dropdown
        self.dropdown = Dropdown(
            width=100,
            height=100,
            options=[
                ft.dropdown.Option("pdf"),
                ft.dropdown.Option("html"),
            ],
        )

        self.archivos_usados = ft.Column(
            [ft.Text('')]
        )

        self.page1 = ft.Column(
            controls=[
                ft.Row(
                    [
                        ft.Container(
                            ft.Text(
                                "Upload your markdown files",
                                size=40,
                                color=ft.colors.ON_SURFACE,
                                weight=ft.FontWeight.W_100,
                            ),
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Container(
                            ElevatedButton(
                                "Seleccionar archivo...",
                                icon=icons.FOLDER_OPEN,
                                on_click=lambda _: self.file_picker.pick_files(allow_multiple=True),
                            )
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        self.archivos_usados
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        self.barra_progreso
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Container(
                            self.dropdown
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Container(
                            self.submit
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ]
        )

        self.direct = ft.TextField(multiline=True, width=300, height=400, min_lines=16, bgcolor=ft.colors.ON_BACKGROUND,
                                   opacity=0.5, color=ft.colors.BACKGROUND)

        self.page2 = ft.Column(
            controls=[
                ft.Container(
                    ft.Row(
                        [
                            ft.Container(
                                ft.TextField(multiline=True, width=300, height=400, min_lines=16,
                                             on_change=self.direct_conversion, bgcolor=ft.colors.ON_BACKGROUND,
                                             opacity=0.5, color=ft.colors.BACKGROUND),
                                width=600,
                                height=400,
                            ),
                            ft.Container(
                                width=80,
                            ),
                            ft.Container(
                                self.direct,
                                width=600,
                                height=400,
                            ),
                            ft.Container(
                                ft.ElevatedButton('Enviar HTML', on_click=lambda event: self.abrir_url())
                            )
                        ],
                        scroll=ft.ScrollMode.ALWAYS
                    ),
                    alignment=ft.alignment.center
                ),
            ],
            visible=False
        )

        self.page.add(self.page1)
        self.page.add(self.page2)

    def abrir_url(self):
        value = self.direct.value

        # Crea un archivo temporal con el nombre "mi_pagina" y extensión ".html"
        temp = tempfile.NamedTemporaryFile(prefix="mi_pagina", suffix=".html", delete=False)

        with open(temp.name, 'wb') as f:
            f.write(value.encode())

        # Proporciona un nombre específico al enviar el archivo al servidor
        files = {'file': ('mi_pagina.html', open(temp.name, 'rb'))}
        requests.post("http://localhost:8000/upload", files=files)

        url_descarga = f'http://localhost:8000/markdown-to-html/mi_pagina.html'
        respuesta = requests.get(url_descarga)

        # Verifica si la solicitud fue exitosa (código de estado 200)
        if respuesta.status_code == 200:
            self.page.launch_url("http://localhost:8000/mi_pagina.html")
        else:
            print(f"Error al descargar la URL. Código de estado: {respuesta.status_code}")

    def direct_conversion(self, event):
        text = event.control.value

        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(text.encode())
            temp_file_name = temp.name

        with open(temp_file_name, 'rb') as f:
            requests.post("http://localhost:8000/upload", files={'file': f})

        # Obtiene el contenido del archivo en formato HTML
        response = requests.get(f'http://localhost:8000/markdown-to-html/{temp_file_name}')
        html_content = response.text

        # Imprime el contenido en HTML
        print(html_content)
        self.direct.value = html_content
        self.page.update()

        # Elimina el archivo temporal
        os.remove(temp_file_name)

    def tabs_changed(self, event):
        self.page1.visible = not self.page1.visible
        self.page2.visible = not self.page2.visible

        self.page.update()

    def file_picker_result(self, e: FilePickerResultEvent):
        if e.files is not None:
            for f in e.files:
                if os.path.splitext(f.name)[1].lower() in ['.md', '.markdown', '.mdown']:
                    self.barra_progreso.visible = True
                    self.page.update()
                    print("FILES: ")
                    print(e.files)
                    print(f)
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
                    self.upload_images_from_markdown(response.text)
                    self.barra_progreso.visible = False
                    self.submit.disabled = False
                    self.page.update()

                    self.archivos_usados.clean()
                    self.añadir_nombres_archivos()

                    self.archivos_usados.update()
                    self.page.update()
                    print(self.archivos)

                else:
                    self.archivos_usados.clean()
                    self.archivos_usados.controls.append(
                        ft.Text(f"No es un archivo markdown: {f.name}", color=ft.colors.RED))
                    self.archivos_usados.update()
                    self.page.update()

    def añadir_nombres_archivos(self):
        self.archivos_usados.clean()
        for archivo2 in self.archivos:
            button = ft.TextButton(f"Nombre del archivo seleccionado: {archivo2}")
            button.on_click = (lambda event, archivo=archivo2: (
                self.archivos.remove(archivo),
                self.archivos_usados.clean(),
                self.añadir_nombres_archivos(),
                self.archivos_usados.update(),
                self.page.update()
            ))
            self.archivos_usados.controls.append(button)

    def upload_images_from_markdown(self, markdown_content):
        # Expresión regular para buscar imágenes en Markdown
        image_regex = r'!\[.*?\]\((.*?)\)'

        # Buscar todas las imágenes en el contenido de Markdown
        images = re.findall(str(image_regex), str(markdown_content))
        print(images)
        # Para cada imagen...
        for image_path in images:
            # Abrir la imagen en modo binario
            with open(image_path, 'rb') as file:
                # Obtener solo el nombre del archivo, sin la ruta completa
                image_name = os.path.basename(image_path)
                print(image_name)

                # Enviar la imagen al servidor
                response = requests.post('http://localhost:8000/upload', files={'file': (image_name, file)})

                # Imprimir la respuesta del servidor
                print(response.text)
                print('SE HA SUBIDO UNA IMAGEN')

    def submit_clicked(self, e):

        if self.dropdown.value == "html":
            for archivo in self.archivos:
                url_descarga = f'http://localhost:8000/markdown-to-html/{archivo}'
                respuesta = requests.get(url_descarga)

                self.page.launch_url(f"http://localhost:8000/mostrar-archivo/{archivo}.html")

        elif self.dropdown.value == "pdf":
            for archivo in self.archivos:
                url_descarga = f'http://localhost:8000/markdown-to-pdf/{archivo}'
                respuesta = requests.get(url_descarga)
                print(url_descarga)

                nombre = archivo.replace(".md", "")

                self.page.launch_url(f"http://localhost:8000/mostrar-archivo/{nombre}.pdf")


def main(page: Page):
    page.title = "Convertidor"
    app = App(page)


ft.app(target=main, view=ft.WEB_BROWSER, upload_dir=carpeta_temporal)
