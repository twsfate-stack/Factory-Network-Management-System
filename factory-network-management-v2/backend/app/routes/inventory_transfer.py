"""Bounded, temporary CSV parsing; reference resolution and atomic import."""
import csv
import hashlib
from collections import defaultdict
from io import StringIO
from pathlib import Path
from flask import Blueprint, Response, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from ..models import db, Switch, SwitchCatalog, ProductionLine
from ..switch_creation import validate_switch_creation
from ..validation import ValidationError
from ..timezone import utcnow, THAILAND_TZ

inventory_transfer = Blueprint("inventory_transfer", __name__)
HEADERS = ['hostname', 'serial_number', 'asset_id', 'switch_model', 'ip_address', 'production_line', 'block', 'firmware', 'mac_address', 'status', 'notes']
EXPORT_HEADERS = HEADERS[:4] + ['vendor', 'model'] + HEADERS[4:] + ['created_at', 'updated_at']
REQUIRED = {'hostname', 'switch_model', 'production_line', 'status'}
MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000
SEARCH_KEYS = ['hostname', 'serial_number', 'asset_id', 'vendor', 'model', 'ip_address', 'production_line', 'block']


def read_upload():
    files = request.files.getlist('file')
    if len(files) != 1 or set(request.files) != {'file'}:
        raise ValidationError('Choose one CSV file.')
    upload = files[0]
    if Path(upload.filename or '').suffix.lower() != '.csv':
        raise ValidationError('Unsupported file format. Use a UTF-8 CSV file.')
    raw = upload.stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValidationError('Import file must be 5 MB or smaller.')
    try:
        content = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValidationError('Unexpected encoding. Save the file as CSV UTF-8 and try again.') from None
    if not content.strip():
        raise ValidationError('The CSV file is empty.')
    if '\x00' in content:
        raise ValidationError('Invalid CSV content. Use a text CSV UTF-8 file.')
    rows = []
    try:
        reader = csv.reader(StringIO(content, newline=''), strict=True)
        headers = [value.strip().lower().replace(' ', '_') for value in next(reader)]
        if len(set(headers)) != len(headers):
            raise ValidationError('Duplicate column headers are not allowed.')
        missing = REQUIRED - set(headers)
        if missing:
            raise ValidationError('Required column(s) missing: ' + ', '.join(sorted(missing)) + '.')
        unknown = set(headers) - set(HEADERS)
        if unknown:
            raise ValidationError('Unsupported column(s): ' + ', '.join(sorted(unknown)) + '. Use the import template; system fields are not accepted.')
        while True:
            line = reader.line_num + 1
            values = next(reader, None)
            if values is None:
                break
            if not values or not any(value.strip() for value in values):
                continue
            if len(values) != len(headers):
                raise ValidationError(f'Row {line}: expected {len(headers)} columns, found {len(values)}.')
            rows.append((line, {key: value.strip() for key, value in zip(headers, values)}))
            if len(rows) > MAX_ROWS:
                raise ValidationError('Import supports up to 5,000 rows per file.')
    except (csv.Error, StopIteration):
        raise ValidationError('Malformed CSV. Check the header, quotes and field lengths.') from None
    if not rows:
        raise ValidationError('The file contains no data rows. Add Switch records below the template header.')
    return rows, hashlib.sha256(raw).hexdigest()


def lookup(values):
    result = defaultdict(list)
    for key, value in values:
        result[key.strip().casefold()].append(value)
    return result


def unique_key(value):
    # Match SQLite NOCASE, which folds ASCII only, including archived records.
    return value.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))


def validate_rows(rows):
    catalogs = lookup(db.session.execute(db.select(SwitchCatalog.name, SwitchCatalog.id)))
    lines = lookup(db.session.execute(db.select(ProductionLine.name, ProductionLine.id)))
    existing = {key: {unique_key(value) for value in db.session.scalars(db.select(getattr(Switch, key))) if value}
                for key in ('serial_number', 'asset_id')}
    occurrences = {key: defaultdict(list) for key in existing}
    for number, row in rows:
        for key in existing:
            if row.get(key):
                occurrences[key][unique_key(row[key])].append(number)
    preview, candidates = [], []
    for number, row in rows:
        errors = []
        body = {key: value for key, value in row.items() if key in HEADERS}
        body['status'] = body.get('status', '').upper()
        body['firmware_version'] = body.pop('firmware', '')
        for field, mapping, target, label in [('switch_model', catalogs, 'catalog_id', 'Switch Model'), ('production_line', lines, 'production_line_id', 'Production Line')]:
            value = row.get(field, '')
            matches = mapping.get(value.casefold(), [])
            if len(matches) != 1:
                errors.append(f'{label} "{value}" ' + ('is ambiguous; use a unique master-data name.' if matches else 'was not found. Create it in master data first.'))
            else:
                body[target] = matches[0]
        for key, label in [('serial_number', 'Serial Number'), ('asset_id', 'Asset ID')]:
            value = row.get(key)
            if value:
                normalized = unique_key(value)
                if normalized in existing[key]:
                    errors.append(f'{label} "{value}" already exists (including Recycle Bin records).')
                if len(occurrences[key][normalized]) > 1:
                    errors.append(f'{label} "{value}" is duplicated in file rows ' + ', '.join(map(str, occurrences[key][normalized])) + '.')
        try:
            values = validate_switch_creation(body)
        except ValidationError as error:
            if str(error) not in errors:
                errors.append(str(error))
        else:
            if not errors:
                candidates.append(values)
        preview.append(dict(row=number, **row, normalized_status=body['status'], errors=errors, result='ERROR' if errors else 'VALID'))
    invalid = sum(bool(row['errors']) for row in preview)
    return dict(total=len(preview), valid=len(preview)-invalid, errors=invalid, rows=preview), candidates


@inventory_transfer.post('/switches/import/preview')
def preview_import():
    rows, fingerprint = read_upload()
    review, _ = validate_rows(rows)
    return jsonify(**review, fingerprint=fingerprint)


@inventory_transfer.post('/switches/import/confirm')
def confirm_import():
    rows, fingerprint = read_upload()
    if request.form.get('fingerprint') != fingerprint:
        raise ValidationError('The file changed. Validate and preview it again before importing.')
    db.session.execute(text('BEGIN IMMEDIATE'))
    review, candidates = validate_rows(rows)
    if review['errors']:
        db.session.rollback()
        return jsonify(success=False, message='No Switches imported. Correct the file or preview it again; some rows are invalid.', **review), 400
    try:
        db.session.add_all([Switch(**values) for values in candidates])
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValidationError('No Switches imported. A record conflicts with existing data. Preview the file again.') from None
    return jsonify(success=True, imported_count=len(candidates)), 201


def safe_cell(value):
    value = '' if value is None else str(value)
    if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')):
        return "'" + value
    return value


def csv_download(headers, rows, filename):
    stream = StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([safe_cell(row.get(key)) for key in headers])
    response = Response(stream.getvalue().encode('utf-8-sig'), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Cache-Control'] = 'no-store'
    return response


@inventory_transfer.get('/switches/import/template')
def import_template():
    return csv_download(HEADERS, [], 'fnms_switch_inventory_template.csv')


@inventory_transfer.get('/switches/export')
def export_inventory():
    format_name = request.args.get('format', 'csv')
    if format_name not in ('csv', 'xlsx'):
        raise ValidationError('Choose CSV or Excel (.xlsx).')
    scope = request.args.get('scope', 'all')
    if scope not in ('all', 'current'):
        raise ValidationError('Choose Export All or Export Current Results.')
    records = [record.to_dict() for record in db.session.scalars(db.select(Switch).where(Switch.is_deleted.is_(False)).order_by(Switch.id))]
    if scope == 'current':
        search = request.args.get('search', '').strip().lower()
        records = [row for row in records if (not search or any(search in str(row.get(key) or '').lower() for key in SEARCH_KEYS))
                   and all(not request.args.get(key) or (row.get(key) or '') == request.args[key] for key in ('production_line', 'status', 'vendor'))]
    if not records:
        raise ValidationError('No Switches match the current filters.' if scope == 'current' else 'No Switches are available to export.')
    for row in records:
        row['switch_model'] = row.get('catalog_name') or f"{row['vendor']} {row['model']}"
    stamp = utcnow().astimezone(THAILAND_TZ).strftime('%Y-%m-%d_%H%M%S')
    if format_name == 'xlsx':
        from ..inventory_excel import excel_download
        return excel_download(records, f"fnms_switch_inventory_{'filtered_' if scope == 'current' else ''}{stamp}.xlsx")
    return csv_download(EXPORT_HEADERS, records, f"fnms_switch_inventory_{'filtered_' if scope == 'current' else ''}{stamp}.csv")
