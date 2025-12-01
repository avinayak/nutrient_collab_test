# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests",
#   "pyjwt",
#   "cryptography",
#   "gunicorn",
#   "flask"
# ]
# ///

import time
import requests
import jwt
from flask import Flask, render_template, jsonify
import uuid
import json

app = Flask(__name__)

# CONFIGURATION
DOC_ENGINE_URL = "https://denghiive.tulv.in/"  # fake self hosted document engine
JWT_SECRET = open("nutrient_private_key.txt").read().strip()  # fake
NUTRIENT_AUTH_TOKEN = "pdf_live_NWt9ZpZIdX0pZnDrLcL7tdjRTIxYA6xgAiylxKpd9Oe"  # fake


@app.route("/")
def home():
    return render_template("index.html")


def get_signature_widgets_instant_json():
    """Returns the Instant JSON configuration for signature widgets."""
    json_str = open("instant_json.json").read()
    return json.loads(json_str)


def build_multipart_body(pdf_path, instant_json):
    """Builds a multipart/form-data body for document upload."""
    boundary = str(uuid.uuid4())

    with open(pdf_path, "rb") as f:
        pdf_content = f.read()

    body_parts = [
        f"--{boundary}",
        f'Content-Disposition: form-data; name="file"; filename="{pdf_path}"',
        "Content-Type: application/pdf",
        "",
        pdf_content.decode("latin1"),
        f"--{boundary}",
        'Content-Disposition: form-data; name="attachment"; filename="instant_json.json"',
        "Content-Type: application/json",
        "",
        json.dumps(instant_json),
        f"--{boundary}--",
    ]

    return "\r\n".join(body_parts).encode("latin1"), boundary


def upload_document_to_engine(pdf_path, instant_json):
    """Uploads a PDF document with Instant JSON to the Document Engine."""
    body, boundary = build_multipart_body(pdf_path, instant_json)

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f'Token token="{NUTRIENT_AUTH_TOKEN}"',
    }

    response = requests.post(
        f"{DOC_ENGINE_URL}api/documents",
        data=body,
        headers=headers,
    )
    response.raise_for_status()

    result = response.json()
    print("Document uploaded:", result)
    return result["data"]["document_id"]


def get_api_headers():
    """Returns standard API headers for Document Engine requests."""
    return {
        "Authorization": f"Bearer {NUTRIENT_AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def configure_form_field_groups(doc_id):
    """Retrieves form fields and updates them with actor group assignments."""
    form_fields_url = f"{DOC_ENGINE_URL}/api/documents/{doc_id}/form-fields"

    response = requests.get(form_fields_url, headers=get_api_headers())
    response.raise_for_status()

    form_fields = response.json()
    annotation_actor_map = extract_annotation_actor_map(form_fields)
    updated_form_fields = apply_actor_groups(annotation_actor_map, form_fields)

    put_form_fields(doc_id, {"formFields": updated_form_fields["data"]})


@app.route("/generate-document", methods=["POST"])
def generate_document():
    """
    Uploads a PDF to Document Engine with signature widgets and configures
    form field groups for buyer/seller roles.
    """
    instant_json = get_signature_widgets_instant_json()
    doc_id = upload_document_to_engine("transfer.pdf", instant_json)
    configure_form_field_groups(doc_id)

    return jsonify({"document_id": doc_id})


def extract_annotation_actor_map(data):
    """
    Given the parsed JSON (dict with 'data' list),
    return a mapping of annotation_id -> actorType.
    """
    mapping = {}

    for item in data.get("data", []):
        # Each item contains widgetAnnotations list
        for widget in item.get("widgetAnnotations", []):
            content = widget.get("content", {})
            annotation_id = widget.get("id")
            actor_type = content.get("customData", {}).get("actorType")

            if annotation_id and actor_type:
                mapping[annotation_id] = actor_type

    return mapping


def apply_actor_groups(actor_map, form_fields):
    """
    Updates the 'group' of each form field and its widget annotations
    based on the actor_map {annotationId: groupName}.
    """
    for field in form_fields.get("data", []):
        annotation_ids = field["content"].get("annotationIds", [])

        # Determine the group for the field (first matching annotation)
        group = None
        for ann_id in annotation_ids:
            if ann_id in actor_map:
                group = actor_map[ann_id]
                break

        # Update form-field-level group
        field["group"] = group

        # Update widget annotations
        for widget in field.get("widgetAnnotations", []):
            widget_id = widget["id"]

            if widget_id in actor_map:
                widget["group"] = actor_map[widget_id]
            else:
                # fallback: check nested content annotation ID
                original_ann_id = widget["content"].get("id")
                if original_ann_id in actor_map:
                    widget["group"] = actor_map[original_ann_id]
                else:
                    widget["group"] = group  # fallback to field-level group

    return form_fields


def put_form_fields(doc_id, form_fields):
    """Updates form fields in the Document Engine."""
    form_fields_url = f"{DOC_ENGINE_URL}api/documents/{doc_id}/form-fields"

    response = requests.put(
        form_fields_url,
        headers=get_api_headers(),
        data=json.dumps(form_fields),
    )
    response.raise_for_status()
    print("PUT form fields response:", response.json())


@app.route("/generate-link/<role>/<doc_id>", methods=["GET"])
def generate_link(role, doc_id):
    """
    Generates a signed JWT with specific permissions for Buyer or Seller.
    """

    token = generate_jwt_token(document_id=doc_id, actor_type=role)

    link = f"/sign/{doc_id}/{token}"
    return jsonify({"link": link})


def generate_jwt_token(document_id: str, actor_type: str):
    """
    Generate an RS256 JWT token similar to the Elixir version.
    Returns: (True, token_string)
    """
    stringified_actor_type = actor_type.upper()

    payload = {
        "document_id": document_id,
        "collaboration_permissions": [
            "annotations:view:all",
            "form-fields:view:all",
            f"form-fields:fill:group={stringified_actor_type}",
        ],
        "permissions": ["read-document", "write", "download"],
        "user_id": stringified_actor_type,
        "default_group": stringified_actor_type,
        "exp": int(time.time()) + 3600,
    }

    private_key = JWT_SECRET

    token = jwt.encode(payload, private_key, algorithm="RS256")

    return token


@app.route("/sign/<doc_id>/<token>")
def sign_page(doc_id, token):
    return render_template(
        "sign.html", doc_id=doc_id, token=token, engine_url=DOC_ENGINE_URL
    )


if __name__ == "__main__":
    app.run(debug=True, port=8000)
