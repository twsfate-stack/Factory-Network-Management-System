from uuid import uuid4
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from .catalog_values import normalize_model_value
from .timezone import utcnow, iso_thailand

db = SQLAlchemy()


class Timestamps:
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class ProductionLine(Timestamps, db.Model):
    __tablename__ = "production_lines"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100, collation="NOCASE"), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False, default="")
    switches = db.relationship("Switch", back_populates="production_line", lazy="selectin")
    model_entries = db.relationship("ProductionLineModel", cascade="all, delete-orphan", lazy="selectin", order_by="ProductionLineModel.position")
    __table_args__ = (db.CheckConstraint("length(trim(name)) > 0"),)


class Switch(Timestamps, db.Model):
    __tablename__ = "switches"
    id = db.Column(db.Integer, primary_key=True)
    catalog_id = db.Column(db.Integer, db.ForeignKey("switch_catalog.id"), index=True)
    catalog = db.relationship("SwitchCatalog", lazy="joined")
    passport_uid = db.Column(db.String(36), nullable=False, default=lambda: str(uuid4()))
    hostname = db.Column(db.String(150), nullable=False)
    asset_id = db.Column(db.String(150, collation="NOCASE"), unique=True)
    serial_number = db.Column(db.String(150, collation="NOCASE"), unique=True)
    vendor = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(150), nullable=False)
    production_line_id = db.Column(db.Integer, db.ForeignKey("production_lines.id"), nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    mac_address = db.Column(db.String(50))
    firmware_version = db.Column(db.String(150))
    block = db.Column(db.String(100))
    notes = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    deleted_at = db.Column(db.DateTime)
    production_line = db.relationship("ProductionLine", back_populates="switches", lazy="joined")
    __table_args__ = (
        db.Index("ux_switches_passport_uid", "passport_uid", unique=True),
        db.CheckConstraint("status IN ('ACTIVE', 'OFFLINE', 'SPARE')"),
        db.CheckConstraint("length(trim(hostname)) > 0"),
        db.CheckConstraint("length(trim(model)) > 0"),
        db.CheckConstraint("length(trim(vendor)) > 0"),
    )

    def to_dict(self):
        result = {column.name: (iso_thailand(getattr(self, column.name)) if column.name in ("created_at", "updated_at", "deleted_at") else getattr(self, column.name)) for column in self.__table__.columns}
        result.update(production_line=self.production_line.name, firmware=self.firmware_version)
        if self.catalog:
            result.update(vendor=self.catalog.vendor, model=self.catalog.model, catalog_name=self.catalog.name)
        else:
            result["catalog_name"] = None
        result["catalog_image_url"] = self.catalog.image_url if self.catalog else None
        return result


class SecuritySettings(Timestamps, db.Model):
    __tablename__ = "security_settings"
    id = db.Column(db.Integer, primary_key=True)
    delete_pin_hash = db.Column(db.Text, nullable=False)
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime)
    __table_args__ = (db.CheckConstraint("id = 1"),)


class ProductionLineModel(db.Model):
    __tablename__ = "production_line_models"
    id = db.Column(db.Integer, primary_key=True)
    production_line_id = db.Column(db.Integer, db.ForeignKey("production_lines.id"), nullable=False)
    model_name = db.Column(db.String(150, collation="NOCASE"), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    __table_args__ = (db.UniqueConstraint("production_line_id", "model_name"), db.CheckConstraint("length(trim(model_name)) > 0"))


class SwitchMoveHistory(db.Model):
    __tablename__ = "switch_move_history"
    id = db.Column(db.Integer, primary_key=True)
    switch_id = db.Column(db.Integer, db.ForeignKey("switches.id"), nullable=False, index=True)
    from_production_line_id = db.Column(db.Integer, db.ForeignKey("production_lines.id"), nullable=False)
    from_production_line_name = db.Column(db.String(100), nullable=False)
    to_production_line_id = db.Column(db.Integer, db.ForeignKey("production_lines.id"), nullable=False)
    to_production_line_name = db.Column(db.String(100), nullable=False)
    from_block = db.Column(db.String(100))
    to_block = db.Column(db.String(100))
    from_hostname = db.Column(db.String(150), nullable=False)
    to_hostname = db.Column(db.String(150), nullable=False)
    moved_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    notes = db.Column(db.Text)

    def to_dict(self):
        return {column.name: iso_thailand(self.moved_at) if column.name == "moved_at" else getattr(self, column.name)
                for column in self.__table__.columns}


class SwitchCatalog(Timestamps, db.Model):
    __tablename__ = "switch_catalog"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(251), nullable=False)
    vendor = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(2000), nullable=False, default="")
    vendor_key = db.Column(db.String(200), nullable=False)
    model_key = db.Column(db.String(300), nullable=False)
    __table_args__ = (db.UniqueConstraint("vendor_key", "model_key"),)

    image_filename = db.Column(db.String(64), nullable=True)

    @property
    def image_url(self):
        return f"/api/media/switch-catalog/{self.image_filename}" if self.image_filename else None

    def to_dict(self, switch_count=0):
        return dict(id=self.id, name=self.name, vendor=self.vendor, model=self.model,
                    description=self.description, switch_count=switch_count, image_url=self.image_url,
                    created_at=iso_thailand(self.created_at), updated_at=iso_thailand(self.updated_at))


@event.listens_for(SwitchCatalog, "before_insert")
@event.listens_for(SwitchCatalog, "before_update")
def catalog_lookup_keys(mapper, connection, catalog):
    catalog.vendor_key = normalize_model_value(catalog.vendor)
    catalog.model_key = normalize_model_value(catalog.model)
