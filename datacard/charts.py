import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os


class Charts:
    def __init__(self, path_csv):
        self.path = path_csv
        self.base_df = self.load_data()
        self.df = self.converting_values(self.base_df)

    def load_data(self):
        df = pd.read_csv(Path(self.path))
        return df

    def converting_values(self, df):
        df_new = df.copy()
        df_new["Latency"] = df_new["Latency"].str.replace(",", ".")
        df_new["Latency"] = df_new["Latency"].astype(np.float64())
        df_new["Latency"] = df_new["Latency"] * 1000
        df_new["Throughput"] = df_new["Throughput"].str.replace(",", ".")
        df_new["Throughput"] = df_new["Throughput"].astype(np.float64())
        df_new["Max_output"] = df_new["Max_output"].str.replace(" ", "")
        df_new["Max_output"] = df_new["Max_output"].astype(np.float64())
        df_new["Context"] = df_new["Context"].str.replace(" ", "")
        df_new["Context"] = df_new["Context"].astype(np.float64()) / 1000
        return df_new

    def plot_creator(self, target, show=False, save_path=None, ylabel=None):
        plt.figure(figsize=(12, 10))
        x = self.base_df["nazwa_modelu"].str.rstrip(":free")
        plt.bar(x, target)
        plt.xticks(rotation=15)
        plt.ylabel(ylabel)
        plt.title(target.name)
        if save_path:
            os.makedirs(save_path, exist_ok=True)
            plt.savefig(
                os.path.join(save_path, f"{target.name}.png"), bbox_inches="tight"
            )
        if show:
            plt.show()
        plt.close()

    def plot_iteration(self):
        df = self.df.copy()
        df = df.drop(labels="nazwa_modelu", axis=1, inplace=False)
        for _ in df.columns:
            self.plot_creator(df[_], save_path="charts", ylabel="Amount")


def main():
    charts = Charts("chartscsv/modele_info_skryba.csv")
    df = charts.df
    print(df["Context"])
    charts.plot_iteration()


if __name__ == "__main__":
    main()
