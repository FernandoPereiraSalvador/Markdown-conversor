import os
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

        # Añadir dropdown
        self.dropdown = Dropdown(
            width=100,
            options=[
                ft.dropdown.Option("pdf"),
                ft.dropdown.Option("html"),
            ],
        )

        self.archivos_usados = None

        self.page1 = ft.Column(
            controls=[
                ft.Row(
                    [
                        ft.Container(
                            ft.Text(
                                "Transformer",
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
                            self.dropdown
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
                                on_click=lambda _: self.file_picker.pick_files(allow_multiple=False),
                            )
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Column(
                            self.archivos_usados
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Container(
                            ElevatedButton(text="Submit", on_click=self.submit_clicked)
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ]
        )
        self.page2 = ft.Text("Página 2", visible=False)

        self.page.add(self.page1)
        self.page.add(self.page2)

    def tabs_changed(self, event):
        self.page1.visible = not self.page1.visible
        self.page2.visible = not self.page2.visible

        self.page.update()

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

        self.archivos_usados = [ft.Text(f"Nombre del archivo seleccionado: {archivo}") for archivo in self.archivos]
        self.page1.update()
        print(self.archivos)

    def submit_clicked(self, e):

        if self.dropdown.value == "html":
            for archivo in self.archivos:
                url_descarga = f'http://localhost:8000/markdown-to-html/{archivo}'
                respuesta = requests.get(url_descarga)

                with open(f'{archivo}.html', 'wb') as f:
                    f.write(respuesta.content)
        elif self.dropdown.value == "pdf":
            for archivo in self.archivos:
                url_descarga = f'http://localhost:8000/markdown-to-pdf/{archivo}'
                respuesta = requests.get(url_descarga)

                with open(f'{archivo}.pdf', 'wb') as f:
                    f.write(respuesta.content)


def main(page: Page):
    page.title = "Convertidor"
    app = App(page)


ft.app(target=main, view=ft.WEB_BROWSER, upload_dir=carpeta_temporal)
