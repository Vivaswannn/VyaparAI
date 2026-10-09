import fitz  # PyMuPDF

def create_detailed_bill():
    doc = fitz.open()
    page = doc.new_page()
    
    text = """=========================================================
                 TAX INVOICE - DETAILED
=========================================================
Vendor: Global Tech Supplies Ltd.
Address: 45 Industrial Estate, Phase 2, New Delhi 110020
GSTIN: 07AABCU9603R1ZM

Invoice Number: GTS-2026-8842
Date of Issue: 2026-10-05
Due Date: 2026-10-20
Payment Status: PENDING
---------------------------------------------------------
Bill To:
VyaparAI Enterprises
100 Startup Hub, IIT Kanpur
---------------------------------------------------------
S.No  Description                       Qty    Rate       Total
1.    Dell XPS 15 Laptops               2      $1500.00   $3000.00
2.    Logitech MX Master 3S Mouse       5      $100.00    $500.00
3.    Mechanical Keyboards              5      $150.00    $750.00
4.    27-inch 4K Monitors               2      $400.00    $800.00
---------------------------------------------------------
Subtotal:                                       $5050.00
Discount (10% festive offer):                  -$505.00
Net Taxable Value:                              $4545.00

IGST (18%):                                     $818.10
---------------------------------------------------------
GRAND TOTAL:                                    $5363.10
=========================================================
Terms & Conditions:
1. Payment must be made within 15 days of invoice date.
2. Late payments will incur a 1.5% monthly interest charge.
3. Make all cheques payable to Global Tech Supplies Ltd.

Thank you for your business!
"""
    
    page.insert_text(fitz.Point(40, 40), text, fontsize=10, fontname="Courier")
    doc.save("detailed_invoice_october.pdf")
    print("Created detailed_invoice_october.pdf")

if __name__ == "__main__":
    create_detailed_bill()
