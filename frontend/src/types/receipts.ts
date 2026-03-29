export interface OCRExtraction {
  id: number;
  receipt_file_id: number;
  raw_text: string | null;
  parsed_fields: Record<string, unknown> | null;
  confidence: number | null;
  engine: string | null;
  created_at: string;
}

export interface ReceiptFile {
  id: number;
  company_id: number;
  employee_id: number;
  file_path: string;
  original_filename: string;
  file_mime_type: string;
  file_size_bytes: number;
  uploaded_at: string;
}

export interface ReceiptUploadResponse {
  receipt_file_id: number;
  receipt: ReceiptFile;
  ocr_extraction: OCRExtraction | null;
}
