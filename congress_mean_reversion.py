from AlgorithmImports import *


class MeanReversionAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2021, 1, 1)
        self.SetEndDate(2024, 1, 1)
        self.SetCash(100000)
        self.lookback = 30  # Days to observe for mean calculation

        # Link to your data source
        url = "https://docs.google.com/spreadsheets/d/13NE0cZQgbABq1Ogbfl8uXCWwg51lU24uE9vg7vk6gB8/gviz/tq?tqx=out:csv"
        self.data = None
        self.DownloadData(url)

    def DownloadData(self, url):
        raw_data = self.Download(url)
        self.data = self.PreprocessData(raw_data)
        self.Debug("Data downloaded and preprocessed. Symbols are being added.")

    def PreprocessData(self, raw_data):
        lines = raw_data.splitlines()
        header = lines[0].split(",")
        processed_data = []

        for line in lines[1:]:
            data = dict(zip(header, line.split(",")))
            data = {
                k.strip('"').strip(): v.strip('"').strip()
                for k, v in data.items()
                if k and v
            }
            processed_data.append(data)
            ticker = data["Ticker"]
            if "/" not in ticker and " " not in ticker:
                if ticker not in self.Securities:
                    self.AddEquity(ticker, Resolution.Daily)

        return processed_data

    def OnData(self, data):
        if not self.data:
            return

        for transaction in self.data:
            ticker = transaction["Ticker"]
            if "/" in ticker or " " in ticker:
                continue

            report_date = self.Time.strptime(
                transaction["ReportDate"], "%Y-%m-%d"
            ).date()
            transaction_type = transaction["Transaction"]

            if self.Time.date() == report_date and self.Securities[ticker].HasData:
                price = self.Securities[ticker].Price
                history = self.History(
                    self.Symbol(ticker), self.lookback, Resolution.Daily
                )

                if history.empty:
                    self.Debug(f"No historical data available for {ticker}")
                    continue

                if "close" not in history.columns:
                    self.Debug(
                        f"No 'close' column available in historical data for {ticker}"
                    )
                    continue

                mean_price = history["close"].mean()

                if transaction_type == "Purchase" and price > 1.05 * mean_price:
                    # If the price is significantly higher post-purchase, anticipate mean reversion
                    self.SetHoldings(ticker, -0.005)
                elif transaction_type == "Sale" and price < 0.95 * mean_price:
                    # If the price is significantly lower post-sale, anticipate recovery
                    self.SetHoldings(ticker, 0.005)
