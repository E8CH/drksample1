import html2canvas from "html2canvas";
import jsPDF from "jspdf";

export function sanitizeFilename(address: string): string {
  return address.replace(/[\\/:*?"<>|]/g, "_").replace(/\s+/g, "_").slice(0, 50);
}

export function generatePdfFilename(address: string): string {
  const d = new Date();
  const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  return `수익분석제안서_${sanitizeFilename(address)}_${dateStr}.pdf`;
}

export async function downloadProposalPDF(
  element: HTMLElement,
  filename: string
): Promise<void> {
  await document.fonts.ready;
  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    logging: false,
    backgroundColor: "#ffffff",
  });
  const imgData = canvas.toDataURL("image/png");
  const pdf = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });
  const pdfWidth = pdf.internal.pageSize.getWidth();
  const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
  pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
  pdf.save(filename);
}
