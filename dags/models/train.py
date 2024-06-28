import logging
import pickle
import tempfile
from io import BytesIO

import numpy as np
from paeio import io
from paeio.path import path_join
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler

from dags import config

logger = logging.getLogger(__name__)


def save_pickle(model, path):
    with tempfile.NamedTemporaryFile() as tfile:
        pickle.dump(model, open(tfile.name, "wb"))
        model_file = open(tfile.name, "rb")
        byte_stream = BytesIO()
        byte_stream.write(model_file.read())
        io.to_any(byte_stream, path)


def train_model():
    equip_data = io.read_excel(
        path_join(config.INPUT_FOLDER, "O_G_Equipment_Data.xlsx")
    )
    equip_data["Fail"] = equip_data["Fail"].replace({False: 0, True: 1})

    # Segregating the continous variables, it will be useful for EDA
    continuous_variables = equip_data.select_dtypes(float).columns

    # We want to PREDICT failures in the equipment, not classify fails,
    # so we need to predict before it happens
    equip_data["Verge_of_failing"] = equip_data["Fail"].shift(-1)

    features_df = equip_data.copy()

    # Also when we know the equipment is failing we should mark as it is about to fail,
    # because if no one comes to fix it, the expectation is that it will keep failing
    features_df["Verge_of_failing"] = np.where(
        (features_df["Fail"] == 1) & (features_df["Verge_of_failing"] != 1),
        1,
        features_df["Verge_of_failing"],
    )

    # Focus on variables that combine the effect of multiple variables at high values
    features_df["Sum_of_variables"] = features_df[continuous_variables].sum(axis=1)
    features_df["Diff_Sum_of_variables"] = features_df["Sum_of_variables"].diff()
    features_df["Diff_acum_Sum_of_variables"] = (
        features_df["Diff_Sum_of_variables"].rolling(4, min_periods=2).sum()
    )

    # Mean avg should be a useful feature if there's a trend pre-fail
    # Rolling std of sum of variables should be a useful feature if variance
    # starts to grow pre-fail
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

    # Per combination of presets
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

    # Using the sum of equip features that are above their 85th percentile
    for col in continuous_variables:
        features_df[f"FLAG_{col}"] = features_df[col] >= equip_data[col].quantile(0.85)
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

    X = features_df[features]
    # filling NA values with -1 because it's the first value and we know it's not a fail
    X[["Sum_of_variables_MA", "Sum_of_variables_std"]] = X[
        ["Sum_of_variables_MA", "Sum_of_variables_std"]
    ].fillna(-1)
    y = features_df["Verge_of_failing"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()
    X_train_lr = scaler.fit_transform(X_train)
    X_test_lr = scaler.transform(X_test)

    lr_model = LogisticRegressionCV(
        solver="liblinear", cv=2, random_state=42, n_jobs=-1
    ).fit(X_train_lr, y_train)

    weights = np.linspace(0, 0.75, 4)
    lr_param_grid = {
        "solver": ["liblinear", "lbfgs"],
        "Cs": [1, 10, 100],
        "class_weight": [{0: x, 1: 1 - x} for x in weights],
    }
    grid_lr = GridSearchCV(lr_model, lr_param_grid, scoring="f1", cv=2, n_jobs=-1).fit(
        X_train_lr, y_train
    )
    grid_lr.best_params_

    grid_lr_model = LogisticRegressionCV(
        solver=grid_lr.best_params_["solver"],
        Cs=grid_lr.best_params_["Cs"],
        class_weight=grid_lr.best_params_["class_weight"],
        cv=2,
        random_state=42,
        n_jobs=-1,
    ).fit(X_train_lr, y_train)

    cm = confusion_matrix(y_test, grid_lr_model.predict(X_test_lr))
    tn, fp, fn, tp = [i for i in cm.ravel()]
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    F1 = 2 * (precision * recall) / (precision + recall)

    logger.info(f"Precision: {precision}\n Recall: {recall}\n F1 Score: {F1}")

    save_pickle(
        grid_lr_model, path_join(config.REFINED_FOLDER, "project1/models/model.pkl")
    )
