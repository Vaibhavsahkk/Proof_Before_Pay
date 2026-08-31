import os
import json
from PIL import Image, ImageDraw, ImageFont

os.makedirs('scratch_test_docs', exist_ok=True)

# Generate a basic image invoice
img = Image.new('RGB', (800, 600), color='white')
d = ImageDraw.Draw(img)
d.text((50, 50), "INVOICE #9999", fill="black")
d.text((50, 100), "Vendor: Acme Corp", fill="black")
d.text((50, 150), "Total: $500.00", fill="black")
d.text((50, 200), "Bank Account: 123456789", fill="black")
img.save('scratch_test_docs/public_invoice.png')

# Generate a basic PDF (just by saving a text file and we'll use a library to convert it or just generate text)
# We can just generate a JSON that acts as our document. The system supports JSON input.
# But for PDF, we can use simple reportlab if it's installed, otherwise we just generate JSON files for now.
try:
    from reportlab.pdfgen import canvas
    c = canvas.Canvas("scratch_test_docs/dummy.pdf")
    c.drawString(100, 750, "INVOICE #9999")
    c.drawString(100, 730, "Vendor: Acme Corp")
    c.drawString(100, 710, "Total: $500.00")
    c.drawString(100, 690, "Bank Account: 123456789")
    c.save()
except ImportError:
    # If reportlab is not there, just create a mock text file
    with open("scratch_test_docs/dummy.txt", "w") as f:
        f.write("INVOICE #9999\nVendor: Acme Corp\nTotal: $500.00\nBank Account: 123456789\n")

# Fresh multi-document pieces
po = {
    "document_type": "purchase_order",
    "po_number": "PO-5555",
    "vendor_name": "Acme Corp",
    "total_amount": 500.00
}
with open("scratch_test_docs/purchase_order.json", "w") as f:
    json.dump(po, f, indent=2)

vendor = {
    "document_type": "vendor_record",
    "vendor_name": "Acme Corp",
    "bank_account": "123456789"
}
with open("scratch_test_docs/vendor_master.json", "w") as f:
    json.dump(vendor, f, indent=2)

# Mismatched documents
invoice_bad_amount = {
    "document_type": "invoice",
    "invoice_number": "INV-777",
    "vendor_name": "Acme Corp",
    "total_amount": 600.00,
    "po_number": "PO-5555"
}
with open("scratch_test_docs/invoice_bad_amount.json", "w") as f:
    json.dump(invoice_bad_amount, f, indent=2)

print("Test documents generated.")
