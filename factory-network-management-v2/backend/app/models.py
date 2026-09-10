from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


class Timestamps:
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class ProductionLine(Timestamps, db.Model):
    __tablename__ = "production_lines"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100, collation="NOCASE"), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False, default="")
    switches = db.relationship("Switch", back_populates="production_line", lazy="selectin")
    __table_args__ = (db.CheckConstraint("length(trim(name)) > 0"),)


class Switch(Timestamps, db.Model):
    __tablename__ = "switches"
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(150), nullable=False)
    asset_id = db.Column(db.String(150, collation="NOCASE"), unique=True)
    serial_number = db.Column(db.String(150, collation="NOCASE"), unique=True)
    vendor = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(150), nullable=False)
    production_line_id = db.Column(db.Integer, db.ForeignKey("production_lines.id"), nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False, index=True)
    ip_address = db.Column(db.String(45), unique=True)
    mac_address = db.Column(db.String(50))
    firmware_version = db.Column(db.String(150))
    notes = db.Column(db.Text)
    production_line = db.relationship("ProductionLine", back_populates="switches")
    __table_args__ = (
        db.CheckConstraint("status IN ('ACTIVE', 'OFFLINE', 'SPARE')"),
        db.CheckConstraint("length(trim(hostname)) > 0"),
        db.CheckConstraint("length(trim(model)) > 0"),
        db.CheckConstraint("length(trim(vendor)) > 0"),
    )

    def to_dict(self):
        return {column.name: (getattr(self, column.name).isoformat() + "Z" if column.name in ("created_at", "updated_at") else getattr(self, column.name)) for column in self.__table__.columns}
