from AlgorithmImports import *


class PelosiTradingAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2021, 1, 1)  # Start date for the algorithm
        self.SetEndDate(2024, 1, 1)  # End date for the algorithm
        self.SetCash(100000)  # Set initial cash to $100,000

        # Link to your data source
        url = "https://docs.google.com/spreadsheets/d/13NE0cZQgbABq1Ogbfl8uXCWwg51lU24uE9vg7vk6gB8/gviz/tq?tqx=out:csv"
        self.pelosi_data = None
        self.DownloadData(url)

        # Set a warm-up period (optional based on strategy)
        self.SetWarmUp(10)

    def DownloadData(self, url):
        raw_data = self.Download(url)
        self.pelosi_data = self.PreprocessData(raw_data)
        self.Debug("Data downloaded and preprocessed. Symbols are being added.")

        # Schedule the event to process transactions when the market is open
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.At(9, 30),
            self.ProcessTransactions,
        )

    def PreprocessData(self, raw_data):
        lines = raw_data.splitlines()
        header = lines[0].split(",")
        processed_data = []

        for line in lines[1:]:
            data = dict(zip(header, line.split(",")))
            # Cleaning and filtering data specifically for Nancy Pelosi
            data = {
                k.strip('"').strip(): v.strip('"').strip()
                for k, v in data.items()
                if k and v
            }
            if data.get("Representative") == "Nancy Pelosi":
                processed_data.append(data)
                ticker = data["Ticker"]
                if ticker not in self.Securities:
                    self.AddEquity(ticker, Resolution.Daily)

        return processed_data

    def ProcessTransactions(self):
        if not self.pelosi_data or self.IsWarmingUp:
            self.Debug("Data is warming up or not yet loaded.")
            return

        today = self.Time.strftime("%Y-%m-%d")
        for data in self.pelosi_data:
            if data["ReportDate"] == today:
                ticker = data["Ticker"]
                trans_type = data["Transaction"]

                if self.Securities[ticker].Price == 0:
                    self.Debug(f"No price data for {ticker} yet.")
                    continue

                if trans_type == "Purchase":
                    self.SetHoldings(ticker, 0.25)
                elif trans_type == "Sale":
                    quantity = self.Portfolio[ticker].Quantity * 0.05
                    self.MarketOrder(ticker, -quantity)
