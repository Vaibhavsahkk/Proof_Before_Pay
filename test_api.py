import requests
import json
import base64
import os
import mimetypes

def encode_file(filepath):
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type:
        mime_type = 'application/octet-stream'
    with open(filepath, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    return {
        "name": os.path.basename(filepath),
        "data": f"data:{mime_type};base64,{data}",
        "type": mime_type
    }

def test_api(files):
    payload = {
        "case_id": "uploaded_bundle",
        "files": files
    }
    url = 'http://localhost:8080/api/investigate'
    response = requests.post(url, json=payload)
    print("Status:", response.status_code)
    try:
        res_json = response.json()
        if "error" in res_json:
            print("ERROR:", res_json["error"])
        result = res_json.get("result", {})
        print("Recommendation:", result.get("recommendation"))
        print("Findings:", result.get("findings"))
        print("Missing Evidence:", result.get("missing_evidence"))
        print("Checks Performed:", res_json.get("checks_performed"))
        print("Checks Skipped:", res_json.get("checks_skipped"))
        print("-" * 50)
    except Exception as e:
        print("Failed to decode json", e)
        print(response.text[:1000])

pdf_file = r'd:\MICRO.1\sources\official_micro1_hackathon.pdf'
img_file = r'd:\MICRO.1\sources\hackathon_announcement.png'

print("--- Testing PDF ---")
test_api([encode_file(pdf_file)])

print("--- Testing Image ---")
test_api([encode_file(img_file)])

print("--- Testing Multiple (PDF + Image) ---")
test_api([encode_file(pdf_file), encode_file(img_file)])
