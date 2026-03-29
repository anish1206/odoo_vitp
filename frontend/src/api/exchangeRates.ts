import { http } from "./http";
import type { ExchangeRatePreview } from "../types/exchangeRates";

interface PreviewParams {
  base_currency: string;
  foreign_currency: string;
  amount: number;
}

export const previewExchangeRate = async (
  params: PreviewParams,
): Promise<ExchangeRatePreview> => {
  const response = await http.get<ExchangeRatePreview>("/exchange_rates/preview", {
    params,
  });
  return response.data;
};
