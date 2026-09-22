"""Explicit Catalog setup for older physical-device regression fixtures."""
def post_switch(client, *, json):
    if isinstance(json, dict) and "catalog_id" not in json:
        data = dict(json)
        vendor, model = data.pop("vendor", None), data.pop("model", None)
        catalogs = client.get("/api/switch-catalog").json
        entry = next((row for row in catalogs if row["vendor"] == vendor and row["model"] == model), None)
        if entry is None:
            response = client.post("/api/switch-catalog", json={"name": f"{vendor} {model}", "vendor": vendor, "model": model})
            if response.status_code != 201:
                return response
            entry = response.json["data"]
        data["catalog_id"] = entry["id"]
        json = data
    return client.post("/api/switches", json=json)
