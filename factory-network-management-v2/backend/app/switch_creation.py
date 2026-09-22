"""Shared physical Switch creation validation for the form and CSV import."""
from ipaddress import ip_address
from .models import db, SwitchCatalog, ProductionLine
from .validation import text_field, ValidationError

STATUSES = {"ACTIVE", "OFFLINE", "SPARE"}


def selected_catalog(catalog_id):
    selected = db.session.get(SwitchCatalog, catalog_id) if type(catalog_id) is int else None
    if selected is None:
        raise ValidationError("Selected switch model does not exist. Select a Switch Model from the catalog.")
    return selected


def validate_switch_creation(body):
    values = {key: text_field(body, key, label, required, maximum) for key, label, required, maximum in [
        ("hostname", "Hostname", True, 150),
        ("asset_id", "Asset ID", False, 150), ("serial_number", "Serial number", False, 150),
        ("ip_address", "IP address", False, 45), ("mac_address", "MAC address", False, 50),
        ("firmware_version", "Firmware", False, 150), ("block", "Block", False, 100), ("notes", "Notes", False, 4000)]}
    status = body.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        raise ValidationError("Status must be ACTIVE, OFFLINE or SPARE.")
    line_id = body.get("production_line_id")
    if type(line_id) is not int or db.session.get(ProductionLine, line_id) is None:
        raise ValidationError("Select an existing Production Line.")
    if values["ip_address"]:
        try:
            values["ip_address"] = str(ip_address(values["ip_address"]))
        except ValueError:
            raise ValidationError("Enter a valid IPv4 or IPv6 address.") from None
    selected = selected_catalog(body.get("catalog_id"))
    return dict(**values, vendor=selected.vendor, model=selected.model, catalog_id=selected.id, status=status, production_line_id=line_id)
