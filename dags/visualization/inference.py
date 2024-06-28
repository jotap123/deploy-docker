import numpy as np
import pandas as pd
from paeio import io
from paeio.path import path_join

from dags import config


def predictions():
    model = io.read_any(
        path_join(config.REFINED_FOLDER, "project1/models/model.pkl"),
        func=pd.read_pickle,
    )

    features_df = io.read_excel(
        path_join(config.INPUT_FOLDER, "O_G_Equipment_Data.xlsx")
    )
    features_df["Fail"] = features_df["Fail"].replace({False: 0, True: 1})
    features_df["Verge_of_failing"] = features_df["Fail"].shift(-1)

    continuous_variables = features_df.select_dtypes(float).columns

    features_df["Verge_of_failing"] = np.where(
        (features_df["Fail"] == 1) & (features_df["Verge_of_failing"] != 1),
        1,
        features_df["Verge_of_failing"],
    )

    features_df["Sum_of_variables"] = features_df[continuous_variables].sum(axis=1)
    features_df["Diff_Sum_of_variables"] = features_df["Sum_of_variables"].diff()
    features_df["Diff_acum_Sum_of_variables"] = (
        features_df["Diff_Sum_of_variables"].rolling(4, min_periods=2).sum()
    )

    features_df["Sum_of_variables_MA"] = (
        features_df["Sum_of_variables"].rolling(4, min_periods=2).mean()
    )
    features_df["Sum_of_variables_std"] = (
        features_df["Sum_of_variables"].rolling(3, min_periods=2).std()
    )

    features_df["Median_Sum_of_variables"] = features_df["Sum_of_variables"].median()
    features_df["Diff_Median_Sum_of_variables"] = (
        features_df["Sum_of_variables"] - features_df["Median_Sum_of_variables"]
    )

    features_df["Median_Sum_of_variables_Preset"] = features_df.groupby(
        ["Preset_1", "Preset_2"]
    )["Sum_of_variables"].transform("median")
    features_df["Diff_Median_Sum_of_variables_Preset"] = (
        features_df["Sum_of_variables"] - features_df["Median_Sum_of_variables_Preset"]
    )

    # Max value of a feature might be useful, although we know individual higher values
    # don't necessarily result in failure
    features_df["Max_value_among_feat"] = np.max(
        features_df[continuous_variables], axis=1
    )
    features_df["Std_equip_features"] = np.std(
        features_df[continuous_variables], axis=1
    )

    features_df["N_equip_feats_abv_85_pct"] = np.sum(
        features_df[features_df.columns[features_df.columns.str.contains("FLAG")]],
        axis=1,
    )

    features = [
        "Sum_of_variables",
        "Sum_of_variables_MA",
        "N_equip_feats_abv_85_pct",
        "Max_value_among_feat",
        "Sum_of_variables_std",
        "Diff_Median_Sum_of_variables_Preset",
        "Diff_Median_Sum_of_variables",
    ]

    features_df["PRED"] = model.predict(features_df[features])

    io.to_parquet(
        features_df,
        path_join(config.REFINED_FOLDER, "project1/results/predictions.parquet"),
    )
