# Catalog image upload

One optional image belongs to SwitchCatalog. Physical Switches resolve catalog_image_url through catalog_id; no image bytes or filename are copied into Switch rows. Passport exposes the same URL. Inventory table columns, Dashboard, Move, status, PIN and QR behavior are unchanged.

## Storage and migration

The additive startup migration adds nullable switch_catalog.image_filename VARCHAR(64) in place. Existing values start NULL. No table rebuild or identity changes. A pre-migration backup is backend/data/factory_network.pre-catalog-images-20260918.db.

Default storage: backend/data/uploads/switch-catalog when using the default SQLite path. More precisely, uploads live beside the configured SQLite database. CATALOG_IMAGE_DIR can override the directory with an absolute path. It is created on the first successful upload. Paths use pathlib and work on Windows or Linux. Set environment variables before starting Flask; .env.example is documentation, not automatically loaded.

Keep the database AND uploads together in backups and transfers. Frontend builds and source updates do not touch uploads. Existing .gitignore excludes backend/data runtime files. If overriding the upload path, keep it outside the source checkout. Future containers can mount the persistent database/upload parent or configure CATALOG_IMAGE_DIR to a mounted volume; no Docker configuration was introduced.

## API

Existing POST /api/switch-catalog and PATCH /api/switch-catalog/:id accept JSON metadata as before or multipart/form-data with name/vendor/model/description and optional image. For removal send multipart remove_image=true. Do not send image and remove_image together. Image filenames from clients are never accepted as database references.

Catalog responses contain image_url (relative API path or null), not server paths. GET /api/media/switch-catalog/:filename serves only generated filenames currently referenced by a Catalog, with image/webp and nosniff headers. Missing files return 404; all image views show a clean placeholder on failure. The frontend resolves media URLs through its existing configured API base URL.

## Validation and save safety

Pillow 12.3.0 validates JPG/JPEG, PNG and WEBP content. Input limit is 5 MiB (5 * 1024 * 1024 bytes); the multipart envelope limit is 6 MiB. Non-upload endpoints retain their existing 64 KiB limit. Corrupt, unsupported, animated and over-20-megapixel images are rejected. Browser extension/size checks are convenience only; backend checks remain authoritative.

The backend verifies and decodes pixels, applies EXIF orientation, strips metadata, and writes one WebP image (quality 90) with a generated UUID filename. No thumbnails, galleries, CDN or Internet downloads. See Pillow's official image validation guidance: https://pillow.readthedocs.io/en/stable/reference/Image.html

A new file is written before the database commit. On database failure the new file is removed and the old reference remains. After a successful replacement/removal, an old file is deleted only if no Catalog references it. Bulk delete uses the same cleanup after commit, preserving the existing PIN and all-Switch-reference protection including Recycle Bin. Cleanup filesystem failures are logged and can leave an unused file; they never remove the saved Catalog reference. An abrupt process/power failure between filesystem and database operations can leave an orphan file, since these are separate storage systems. No automatic directory-wide cleanup is performed.

## UI

Add/Edit Model uses local preview before Save, Upload/Change/Remove controls, and existing form styling. Cancel revokes preview resources without sending a mutation. Saving disables duplicate submission. The Catalog list has a compact thumbnail beside Model Name, retaining all five columns and selection behavior. Catalog View, Switch View, and Passport show a modest aspect-preserving image. Add/Edit physical Switch forms have no upload control.

## Validation

71 backend tests passed, covering JPG/PNG/WEBP, optional images, unsupported/corrupt/oversized uploads, safe media URLs, rollback and filesystem failure, replacement/removal, restart/missing-file/migration, shared references, Switch model changes, Move/status/delete/restore and protected Catalog deletion. Existing Dashboard/Production Line/PIN/Passport regressions passed.

Isolated browser tests covered preview/cancel/remove-pending, create, thumbnail/View, replace/cancel/remove, invalid extension, shared Switch View/Passport, missing-file fallback and mobile layout. Frontend lint and production build passed. Tests use separate temporary databases, not live factory records.
