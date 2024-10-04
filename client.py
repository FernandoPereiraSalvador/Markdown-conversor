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

from client_constantes import IP, PORT

CARPETA_TEMPORAL = tempfile.mkdtemp()
os.environ['FLET_SECRET_KEY'] = 'secret'

class App:
    def __init__(self, page):

        # Inicialización de atributos
        self.page = page
        self.file_picker = FilePicker()
        self.archivos = []

        self.filter = ft.Tabs(
            scrollable=False,
            selected_index=0,
            on_change=self.tabs_changed,
            tabs=[ft.Tab(text="Upload files"), ft.Tab(text="Direct")],
        )

        # Crea elementos de la interfaz grafica para tener una referencia

        self.page.add(self.filter)

        self.file_picker.on_result = self.file_picker_result

        self.page.overlay.append(self.file_picker)

        self.submit = ElevatedButton(text="Submit", on_click=self.submit_clicked,
                                     disabled=True)

        self.barra_progreso_archivos = ft.ProgressBar(width=250, color="blue", bgcolor="#eeeeee", visible=False)
        self.barra_progreso_render = ft.ProgressBar(width=250, color="blue", bgcolor="#eeeeee", visible=False)
        self.barra_progreso_transform = ft.ProgressBar(width=250, color="blue", bgcolor="#eeeeee", visible=False)

        self.boton_render = ft.Container(
                                ft.ElevatedButton('Render HTML', on_click=lambda event: self.abrir_url())
                            )

        self.dropdown = Dropdown(
            width=100,
            options=[
                ft.dropdown.Option("pdf"),
                ft.dropdown.Option("html"),
            ],
        )

        self.archivos_usados = ft.Column(
            [ft.Text('')]
        )

        self.direct = ft.TextField(multiline=True, width=300, height=400, min_lines=16, bgcolor=ft.colors.ON_BACKGROUND,
                                   opacity=0.5, color=ft.colors.BACKGROUND)


        # Configuración de la interfaz para "Upload files"
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
                        self.barra_progreso_archivos
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Container(
                            self.dropdown,
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
                ),
                ft.Row(
                    [
                        ft.Container(
                            self.barra_progreso_transform
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ]
        )

        # Configuración de la interfaz para "Direct"
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

                        ],
                        scroll=ft.ScrollMode.ALWAYS
                    ),
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.Row(
                        [
                            ft.Container(
                                width=950,
                            ),
                            ft.Container(
                                self.barra_progreso_render,
                            ),
                        ]
                    ),
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.Row(
                        [
                            ft.Container(
                                width=1000,
                            ),
                            self.boton_render

                        ]
                    ),
                    alignment=ft.alignment.center
                ),
            ],
            visible=False
        )

        self.page.add(self.page1)
        self.page.add(self.page2)

    def abrir_url(self):
        """
        Abre el html generado a partir del código que ha introducido el usuario en la ventana direct
        :return:
        """

        # Activa la barra de progreso y actualiza la interfaz gráfica
        self.barra_progreso_render.visible = True
        self.page.update()

        # Obtiene el contenido HTML del área designada
        value = self.direct.value

        # Crea un archivo temporal con el nombre "mi_pagina" y extensión ".html"
        temp = tempfile.NamedTemporaryFile(prefix="mi_pagina", suffix=".html", delete=False)

        # Guarda el contenido HTML en el archivo temporal
        with open(temp.name, 'wb') as f:
            f.write(value.encode())

        # Proporciona un nombre específico al enviar el archivo al servidor
        files = {'file': ('mi_pagina.html', open(temp.name, 'rb'))}
        requests.post(f"http://{IP}:{PORT}/upload", files=files)

        # Obtiene la URL de descarga
        url_descarga = f'http://{IP}:{PORT}/markdown-to-html/mi_pagina.html'
        respuesta = requests.get(url_descarga)

        # Verifica si la solicitud fue exitosa (código de estado 200)
        if respuesta.status_code == 200:
            self.page.launch_url(f"http://{IP}:{PORT}/mi_pagina.html")
        else:
            print(f"Error al descargar la URL. Código de estado: {respuesta.status_code}")

        # Desactiva la barra de progreso y actualiza la interfaz gráfica
        self.barra_progreso_render.visible = False
        self.page.update()

    def direct_conversion(self, event):
        """
         Realiza una conversión directa del contenido Markdown a HTML en directo

        :param event: El objeto de evento asociado al evento de conversión directa.
        :return: None
        """

        # Activa la barra de progreso y deshabilita el botón de renderización
        self.barra_progreso_render.visible = True
        self.boton_render.disabled = True
        self.page.update()

        # Obtiene el codigo markdown que ha introducido el usuario
        text = event.control.value

        # Guarda temporalmente el contenido como un archivo Markdown
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(text.encode())
            temp_file_name = temp.name

        # Sube el archivo al servidor
        with open(temp_file_name, 'rb') as f:
            requests.post(f"http://{IP}:{PORT}/upload", files={'file': f})

        # Obtiene el contenido del archivo en formato HTML
        response = requests.get(f'http://{IP}:{PORT}/markdown-to-html-direct/{temp_file_name}')
        html_content = response.text

        # Imprime el contenido en HTML
        self.direct.value = html_content
        self.page.update()

        # Elimina el archivo temporal
        os.remove(temp_file_name)

        # Desactiva la barra de progreso y habilita el botón de renderización
        self.barra_progreso_render.visible = False
        self.boton_render.disabled = False
        self.page.update()

    def tabs_changed(self, event):
        """
        Maneja el cambio de pestañas entre la pagina para subir archivos y la de direct
        :param event: El objeto de evento asociado al cambio de pestañas.
        :return: None
        """
        self.page1.visible = not self.page1.visible
        self.page2.visible = not self.page2.visible

        self.page.update()

    def file_picker_result(self, e: FilePickerResultEvent):
        """
        Maneja el resultado de la selección de archivos a través de un FilePicker.

        :param e: El objeto de evento asociado al cambio de pestañas.
        :return: None
        """
        # Verifica si se han seleccionado archivos
        if e.files is not None:
            # Itera los archivos seleccionados
            for f in e.files:
                # Comprueba si es un archivo markdwon
                if os.path.splitext(f.name)[1].lower() in ['.md', '.markdown', '.mdown']:

                    # Muestra la barra de progreso y deshabilita el botón de envío
                    self.barra_progreso_archivos.visible = True
                    self.submit.disabled = True
                    self.page.update()

                    # Añade el nombre del archivo a la lista de archivos
                    self.archivos.append(f.name)

                    # Sube el archivo al servidor
                    upload_url = self.page.get_upload_url(f.name, 60)
                    upload_file = FilePickerUploadFile(f.name, upload_url)
                    self.file_picker.upload([upload_file])

                    # Obtiene la ruta de la carpeta temporal
                    archivo_en_carpeta = os.path.join(CARPETA_TEMPORAL, f.name)

                    # Esperamos 1 segundo a que el archivo temporal este creado
                    time.sleep(1)

                    # Abre el archivo en modo binario y lo envía al servidor
                    with open(archivo_en_carpeta, 'rb') as file:
                        requests.post(f"http://{IP}:{PORT}/upload", files={'file': file})

                    # Enviar una solicitud al servidor para obtener el contenido del archivo
                    response = requests.get(f'http://{IP}:{PORT}/upload/{f.name}')

                    # Realiza el manejo de las imágenes en el contenido markdown
                    self.upload_images_from_markdown(response.text)

                    # Oculta la barra de progreso y habilita el botón de envío
                    self.barra_progreso_archivos.visible = False
                    self.submit.disabled = False
                    self.page.update()

                    # Actualiza la interfaz
                    self.archivos_usados.clean()
                    self.anadir_nombres_archivos()
                    self.archivos_usados.update()
                    self.page.update()

                else:
                    # Muestra un mensaje indicando que no es un archivo markdown
                    self.archivos_usados.clean()
                    self.archivos_usados.controls.append(
                        ft.Text(f"No es un archivo markdown: {f.name}", color=ft.colors.RED))
                    self.archivos_usados.update()
                    self.page.update()

    def anadir_nombres_archivos(self):
        """
        Añade los nombres de los archivos al contenedor `archivos_usados` y actualiza la interfaz gráfica.

        Cuando se hace click sobre uno se borra y actualiza la interfaz gráfica de forma recursiva
        :return: None
        """
        # Limpia el contenedor de archivos usados
        self.archivos_usados.clean()

        # Iteremos a traves de archivos
        for archivo2 in self.archivos:
            button = ft.TextButton(f"Nombre del archivo seleccionado: {archivo2}")
            button.on_click = (lambda event, archivo=archivo2: (
                self.archivos.remove(archivo),
                self.archivos_usados.clean(),
                self.anadir_nombres_archivos(),
                self.archivos_usados.update(),
                self.page.update()
            ))
            self.archivos_usados.controls.append(button)

    def upload_images_from_markdown(self, markdown_content):
        """
        Sube las imágenes encontradas en el contenido de Markdown al servidor.

        :param markdown_content: El contenido de Markdown que contiene las imágenes.
        :return: None

        """
        # Expresión regular para buscar imágenes en Markdown
        image_regex = r'!\[.*?\]\((.*?)\)'

        # Buscar todas las imágenes en el contenido de Markdown
        images = re.findall(str(image_regex), str(markdown_content))

        # Iterar a traves de imagenes
        for image_path in images:

            # Abrir la imagen en modo binario
            with open(image_path, 'rb') as file:

                # Obtener solo el nombre del archivo, sin la ruta completa
                image_name = os.path.basename(image_path)
                print(image_name)

                # Enviar la imagen al servidor
                response = requests.post(f'http://{IP}:{PORT}/upload', files={'file': (image_name, file)})


    def submit_clicked(self, e):
        """
        Maneja el evento de clic en el botón de envío.

        :param e: El objeto de evento asociado al clic del botón.
        :return: None
        """

        # Hace visible la barra de progreso y actualiza la página.
        self.barra_progreso_transform.visible = True
        self.page.update()

        # Comprueba el valor seleccionado en el menú desplegable.
        if self.dropdown.value == "html":
            for archivo in self.archivos:

                # Itera sobre los archivos y realiza la conversión a HTML.
                url_descarga = f'http://{IP}:{PORT}/markdown-to-html/{archivo}'
                respuesta = requests.get(url_descarga)

                # Abre la URL en el navegador para descargar el archivo HTML.
                self.page.launch_url(f"http://{IP}:{PORT}/mostrar-archivo/{archivo}.html")

        elif self.dropdown.value == "pdf":
            # Itera sobre los archivos y realiza la conversión a PDF.
            for archivo in self.archivos:
                url_descarga = f'http://{IP}:{PORT}/markdown-to-pdf/{archivo}'
                respuesta = requests.get(url_descarga)

                # Obtiene el nombre del archivo sin la extensión ".md".
                nombre = archivo.replace(".md", "")

                # Abre la URL en el navegador para descargar el archivo PDF.
                self.page.launch_url(f"http://{IP}:{PORT}/mostrar-archivo/{nombre}.pdf")

        # Oculta la barra de progreso y actualiza la página.
        self.barra_progreso_transform.visible = False
        self.page.update()


def main(page: Page):
    page.title = "Convertidor"
    App(page)


ft.app(target=main, view=ft.AppView.WEB_BROWSER, upload_dir=CARPETA_TEMPORAL)
