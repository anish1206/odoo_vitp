export interface ExchangeRatePreview {
  base_currency: string;
  foreign_currency: string;
  amount: number;
  converted_amount: number;
  rate: number;
  provider: string;
  as_of: string;
}
