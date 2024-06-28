from AlgorithmImports import *


class PelosiTradingAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2024, 1, 1)
        self.SetCash(100000)
        self.party = "R"  # Party to filter on (R = Republican, D = Democrat)

        # Link to your data source
        url = "https://docs.google.com/spreadsheets/d/13NE0cZQgbABq1Ogbfl8uXCWwg51lU24uE9vg7vk6gB8/gviz/tq?tqx=out:csv"
        self.data = None
        self.DownloadData(url)

    def DownloadData(self, url):
        raw_data = self.Download(url)
        self.data = self.PreprocessData(raw_data, self.party)
        self.Debug("Data downloaded and preprocessed. Symbols are being added.")

        # Schedule the event to process transactions when the market is open
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.At(9, 30),
            self.ProcessTransactions,
        )

    def PreprocessData(self, raw_data, party):
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
            if data.get("Party") == party:
                processed_data.append(data)
                ticker = data["Ticker"]
                if "/" not in ticker and " " not in ticker:
                    if ticker not in self.Securities:
                        self.AddEquity(ticker, Resolution.Daily)

        return processed_data

    def ProcessTransactions(self):
        if not self.data or self.IsWarmingUp:
            self.Debug("Data is warming up or not yet loaded.")
            return

        today = self.Time.strftime("%Y-%m-%d")
        for data in self.data:
            if data["ReportDate"] == today:
                ticker = data["Ticker"]
                transaction_type = data["Transaction"]

                if transaction_type == "Purchase":
                    self.SetHoldings(ticker, 0.2)
                elif transaction_type == "Sale":
                    self.SetHoldings(ticker, -0.05)
                elif transaction_type == "Sale (Partial)":
                    self.SetHoldings(ticker, -0.1)
                elif transaction_type == "Sale (Full)":
                    self.liquidate(ticker)
