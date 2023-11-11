import flet
from flet import (
    ElevatedButton,
    FilePicker,
    FilePickerResultEvent,
    Page,
    Text,
    icons,
)

def main(page: Page):
    file_picker = FilePicker()
    file_name = None

    def file_picker_result(e: FilePickerResultEvent):
        nonlocal file_name
        if e.files is not None:
            file_name = e.files[0].name
            page.add(Text(f"Nombre del archivo seleccionado: {file_name}"))
        page.update()

    file_picker.on_result = file_picker_result

    # hide dialog in a overlay
    page.overlay.append(file_picker)

    page.add(
        ElevatedButton(
            "Seleccionar archivo...",
            icon=icons.FOLDER_OPEN,
            on_click=lambda _: file_picker.pick_files(allow_multiple=False),
        ),
    )

flet.app(target=main, view=flet.WEB_BROWSER)
