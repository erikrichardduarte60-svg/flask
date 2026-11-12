import os
import uuid
from flask import current_app
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def save_upload(file):
    """Salva a imagem em static/uploads e devolve o nome do arquivo.
    Devolve None se nenhum arquivo foi enviado.
    Levanta ValueError se o arquivo for inválido."""

    if file is None or file.filename == "":
        return None

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Formato não permitido. Use png, jpg, jpeg, gif ou webp.")

    try:
        Image.open(file.stream).verify()
    except (UnidentifiedImageError, OSError):
        raise ValueError("O arquivo enviado não é uma imagem válida.")

    file.stream.seek(0)  # verify() consome o stream, então voltamos ao início

    unique_name = f"{uuid.uuid4().hex}_{filename}"

    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name))

    return unique_name


def delete_upload(filename):
    """Apaga um arquivo de upload, se ele existir."""

    if not filename:
        return

    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    if os.path.exists(path):
        os.remove(path)