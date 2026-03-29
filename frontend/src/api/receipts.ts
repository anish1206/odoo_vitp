import { http } from "./http";
import type { OCRExtraction, ReceiptFile, ReceiptUploadResponse } from "../types/receipts";

export const uploadReceipt = async (file: File): Promise<ReceiptUploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await http.post<ReceiptUploadResponse>("/receipts", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const getReceipt = async (receiptId: number): Promise<ReceiptFile> => {
  const response = await http.get<ReceiptFile>(`/receipts/${receiptId}`);
  return response.data;
};

export const getReceiptOcr = async (receiptId: number): Promise<OCRExtraction> => {
  const response = await http.get<OCRExtraction>(`/receipts/${receiptId}/ocr`);
  return response.data;
};
