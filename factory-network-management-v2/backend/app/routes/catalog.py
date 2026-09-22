from flask import Blueprint, jsonify
from sqlalchemy import func, text
from .security import begin_write, verify_pin
from ..catalog_images import catalog_request, save_catalog, cleanup_unreferenced
from ..models import db, Switch, SwitchCatalog
from ..catalog_values import normalize_model_value
from ..validation import json_body, text_field, ValidationError

catalog = Blueprint("catalog", __name__)


def usage_count(catalog_id):
    return db.session.scalar(db.select(func.count(Switch.id)).where(Switch.catalog_id == catalog_id, Switch.is_deleted.is_(False)))


def catalog_fields(body):
    return dict(name=text_field(body, "name", "Model Name", True, 251),
                vendor=text_field(body, "vendor", "Vendor", True, 100),
                model=text_field(body, "model", "Model", True, 150),
                description=text_field(body, "description", "Description", maximum=2000) or "")


def check_duplicate(values, excluding=None):
    existing = db.session.scalar(db.select(SwitchCatalog.id).where(
        SwitchCatalog.vendor_key == normalize_model_value(values["vendor"]),
        SwitchCatalog.model_key == normalize_model_value(values["model"])))
    if existing is not None and existing != excluding:
        raise ValidationError("This switch model already exists in the catalog.")


@catalog.get("/switch-catalog")
def list_catalog():
    query = db.select(SwitchCatalog, func.count(Switch.id)).outerjoin(Switch,
        db.and_(Switch.catalog_id == SwitchCatalog.id, Switch.is_deleted.is_(False))).group_by(SwitchCatalog.id).order_by(SwitchCatalog.name)
    return jsonify([entry.to_dict(count) for entry, count in db.session.execute(query)])


@catalog.post("/switch-catalog")
def create_catalog():
    body, image_bytes, remove = catalog_request()
    values = catalog_fields(body)
    db.session.execute(text("BEGIN IMMEDIATE"))
    check_duplicate(values)
    entry = SwitchCatalog(**values)
    save_catalog(entry, image_bytes, remove)
    return jsonify(success=True, data=entry.to_dict()), 201


@catalog.get("/switch-catalog/<int:catalog_id>")
def get_catalog(catalog_id):
    entry = db.session.get(SwitchCatalog, catalog_id)
    if entry is None:
        return jsonify(success=False, message="Switch model not found."), 404
    return jsonify(entry.to_dict(usage_count(catalog_id)))


@catalog.patch("/switch-catalog/<int:catalog_id>")
def edit_catalog(catalog_id):
    body, image_bytes, remove = catalog_request()
    db.session.execute(text("BEGIN IMMEDIATE"))
    entry = db.session.get(SwitchCatalog, catalog_id)
    if entry is None:
        db.session.rollback()
        return jsonify(success=False, message="Switch model not found."), 404
    values = catalog_fields({key: body.get(key, getattr(entry, key)) for key in ("name", "vendor", "model", "description")})
    check_duplicate(values, entry.id)
    for key, value in values.items():
        setattr(entry, key, value)
    save_catalog(entry, image_bytes, remove)
    return jsonify(success=True, data=entry.to_dict(usage_count(entry.id)))


def deletion_ids(body):
    ids = body.get("ids")
    if (not isinstance(ids, list) or not 1 <= len(ids) <= 500
            or any(type(value) is not int or value < 1 for value in ids) or len(set(ids)) != len(ids)):
        raise ValidationError("Select between 1 and 500 distinct switch models.")
    return ids


def deletion_review(ids):
    # Count ALL references, including archived switches, to protect later Restore.
    query = db.select(SwitchCatalog.id, SwitchCatalog.name, func.count(Switch.id),
        func.sum(db.case((Switch.is_deleted.is_(True), 1), else_=0))).outerjoin(
        Switch, Switch.catalog_id == SwitchCatalog.id).where(SwitchCatalog.id.in_(ids)).group_by(SwitchCatalog.id).order_by(SwitchCatalog.name)
    rows = db.session.execute(query).all()
    if len(rows) != len(ids):
        raise ValidationError("One or more switch models are unavailable. Refresh the catalog and try again.")
    eligible, blocked = [], []
    for catalog_id, name, count, deleted_count in rows:
        entry = dict(id=catalog_id, name=name)
        if count:
            blocked.append(dict(**entry, switch_count=count, deleted_switch_count=deleted_count,
                reason=f"Used by {count} physical switch(es)" + (f", including {deleted_count} in Recycle Bin." if deleted_count else ".")))
        else:
            eligible.append(entry)
    return eligible, blocked


@catalog.post("/switch-catalog/delete-preview")
def preview_catalog_delete():
    eligible, blocked = deletion_review(deletion_ids(json_body()))
    response = jsonify(eligible=eligible, blocked=blocked)
    response.headers["Cache-Control"] = "no-store"
    return response


@catalog.post("/switch-catalog/delete")
def delete_catalogs():
    body = json_body()
    ids = deletion_ids(body)
    begin_write()
    verify_pin(body)
    eligible, blocked = deletion_review(ids)
    filenames = []
    if eligible:
        filenames = db.session.scalars(db.select(SwitchCatalog.image_filename).where(SwitchCatalog.id.in_([row["id"] for row in eligible]))).all()
        db.session.execute(db.delete(SwitchCatalog).where(SwitchCatalog.id.in_([row["id"] for row in eligible])))
    db.session.commit()
    cleanup_unreferenced(filenames)
    return jsonify(success=True, deleted=eligible, blocked=blocked)
