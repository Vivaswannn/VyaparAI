import fitz  # PyMuPDF

def create_invoice(filename, vendor, inv_num, date, due_date, amount, status):
    doc = fitz.open()
    page = doc.new_page()
    
    text = f"""INVOICE / TAX INVOICE
=========================================
Vendor: {vendor}
Invoice Number: {inv_num}
Date of Issue: {date}
Due Date: {due_date}

Description                     Amount
-----------------------------------------
Consulting Services             ${amount - 100:.2f}
Software License                $100.00

-----------------------------------------
Subtotal:                       ${amount:.2f}
Tax (GST 18%):                  ${amount * 0.18:.2f}
TOTAL AMOUNT:                   ${amount * 1.18:.2f}

Payment Status: {status}
=========================================
Thank you for your business.
"""
    
    page.insert_text(fitz.Point(50, 50), text, fontsize=12, fontname="Courier")
    doc.save(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    # Create an overdue invoice
    create_invoice("demo_invoice_overdue.pdf", "Acme Corp India", "INV-2026-001", "2026-09-01", "2026-09-15", 1000.00, "OVERDUE")
    
    # Create a paid invoice
    create_invoice("demo_invoice_paid.pdf", "TechSolutions Pvt Ltd", "INV-2026-002", "2026-10-01", "2026-10-15", 500.00, "PAID")
