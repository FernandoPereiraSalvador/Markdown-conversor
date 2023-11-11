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
                # requests.post("http://localhost:8000/upload", files={'file': e.data})
                # Enviar una solicitud al servidor para obtener el contenido del archivo
                response = requests.get(f'http://localhost:8000/upload/{f.name}')
                print(response.text)
                self.page.add(Text(f"Nombre del archivo seleccionado: {f.name}"))
        self.page.update()

    def submit_clicked(self, e):
        if self.dropdown.value == "html":
            for archivo in self.archivos:
                self.convert_md_to_html(archivo)

    def convert_md_to_html(self, archivo):
        # Enviar una solicitud al servidor para obtener el contenido del archivo
        print("Convertir")


def main(page: Page):
    app = App(page)


flet.app(target=main, view=flet.WEB_BROWSER, upload_dir="upload")
