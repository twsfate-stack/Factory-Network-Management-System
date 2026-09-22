"""Catalog-owned runtime images; files are published only by committed DB references."""
from io import BytesIO
from pathlib import Path
import re
import warnings
from uuid import uuid4
from flask import Blueprint, current_app, request, send_from_directory, abort
from PIL import Image, ImageOps, UnidentifiedImageError
from .models import db, SwitchCatalog
from .validation import ValidationError, json_body, commit_record

media = Blueprint("media", __name__)
MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 20_000_000
SAFE_NAME = re.compile(r"[0-9a-f]{32}\.webp\Z")


def catalog_request():
    if request.mimetype != "multipart/form-data":
        return json_body(), None, False
    if set(request.files) - {"image"} or len(request.files.getlist("image")) > 1:
        raise ValidationError("Upload one primary image only.")
    remove = request.form.get("remove_image", "false")
    if remove not in ("true", "false"):
        raise ValidationError("Invalid remove image option.")
    upload = request.files.get("image")
    if upload and remove == "true":
        raise ValidationError("Choose either a replacement image or Remove Image.")
    return request.form.to_dict(), validate_image(upload) if upload else None, remove == "true"


def validate_image(upload):
    if Path(upload.filename or "").suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValidationError("Unsupported image format. Use JPG, PNG or WEBP.")
    raw = upload.stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValidationError("Image must be 5 MB or smaller.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw), formats=["JPEG", "PNG", "WEBP"]) as source:
                if source.width * source.height > MAX_PIXELS:
                    raise ValidationError("Image dimensions must be 20 megapixels or smaller.")
                if getattr(source, "n_frames", 1) != 1:
                    raise ValidationError("Use a single still image, not an animation.")
                source.verify()
            with Image.open(BytesIO(raw), formats=["JPEG", "PNG", "WEBP"]) as source:
                source.load()
                oriented = ImageOps.exif_transpose(source)
                # Re-encode pixels only: no uploaded metadata or appended executable content.
                clean = oriented.convert("RGBA" if "A" in oriented.getbands() or "transparency" in source.info else "RGB")
                clean.info.clear()
                output = BytesIO()
                clean.save(output, format="WEBP", quality=90)
                return output.getvalue()
    except ValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise ValidationError("Invalid or corrupted image. Choose a valid JPG, PNG or WEBP file.") from None


def remove_file(filename):
    if not filename or not SAFE_NAME.fullmatch(filename):
        return
    try:
        (current_app.config["CATALOG_IMAGE_DIR"] / filename).unlink(missing_ok=True)
    except OSError:
        current_app.logger.warning("Catalog image cleanup could not remove file %s", filename)


def cleanup_unreferenced(filenames):
    for filename in set(filenames) - {None}:
        if not db.session.scalar(db.select(SwitchCatalog.id).where(SwitchCatalog.image_filename == filename).limit(1)):
            remove_file(filename)


def save_catalog(entry, image_bytes, remove=False):
    old = entry.image_filename
    filename = None
    try:
        if image_bytes is not None:
            folder = current_app.config["CATALOG_IMAGE_DIR"]
            folder.mkdir(parents=True, exist_ok=True)
            filename = uuid4().hex + ".webp"
            with (folder / filename).open("xb") as output:
                output.write(image_bytes)
            entry.image_filename = filename
        elif remove:
            entry.image_filename = None
        commit_record(entry)
    except OSError:
        db.session.rollback()
        remove_file(filename)
        raise ValidationError("Unable to save the image. Check server upload storage permissions and try again.") from None
    except Exception:
        db.session.rollback()
        remove_file(filename)
        raise
    if old and (image_bytes is not None or remove):
        cleanup_unreferenced([old])


@media.get("/media/switch-catalog/<filename>")
def catalog_image(filename):
    if not SAFE_NAME.fullmatch(filename):
        abort(404)
    if not db.session.scalar(db.select(SwitchCatalog.id).where(SwitchCatalog.image_filename == filename).limit(1)):
        abort(404)
    folder = current_app.config["CATALOG_IMAGE_DIR"]
    path = folder / filename
    if path.is_symlink() or not path.is_file():
        abort(404)
    response = send_from_directory(folder, filename, mimetype="image/webp", conditional=True, max_age=86400)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
