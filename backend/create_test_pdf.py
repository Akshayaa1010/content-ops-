from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font('helvetica', size=15)
pdf.cell(200, 10, txt='Test PDF for extraction', new_x='LMARGIN', new_y='NEXT', align='C')
pdf.output('test.pdf')
