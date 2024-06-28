import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import auc, confusion_matrix, roc_curve


def evalBinaryClassifier(model, x, y, labels=["Positives", "Negatives"]):
    """
    Visualize the performance of  a Logistic Regression Binary Classifier.

    Displays a labelled Confusion Matrix, distributions of the predicted
    probabilities for both classes, the ROC curve, and F1 score of a fitted
    Binary Logistic Classifier. Author: gregcondit.com/articles/logr-charts

    Parameters
    ----------
    model : fitted scikit-learn model with predict_proba & predict methods
        and classes_ attribute. Typically LogisticRegression or
        LogisticRegressionCV

    x : {array-like, sparse matrix}, shape (n_samples, n_features)
        Training vector, where n_samples is the number of samples
        in the data to be tested, and n_features is the number of features

    y : array-like, shape (n_samples,)
        Target vector relative to x.

    labels: list, optional
        list of text labels for the two classes, with the positive label first

    Displays
    ----------
    3 Subplots

    Returns
    ----------
    F1: float
    """
    # model predicts probabilities of positive class
    p = model.predict_proba(x)
    if len(model.classes_) != 2:
        raise ValueError("A binary class problem is required")
    if model.classes_[1] == 1:
        pos_p = p[:, 1]
    elif model.classes_[0] == 1:
        pos_p = p[:, 0]

    # FIGURE
    plt.figure(figsize=[20, 5])

    # 1 -- Confusion matrix
    cm = confusion_matrix(y, model.predict(x))
    plt.subplot(131)
    ax = sns.heatmap(
        cm, annot=True, cmap="Blues", cbar=False, annot_kws={"size": 14}, fmt="g"
    )
    cmlabels = [
        "True Negatives",
        "False Positives",
        "False Negatives",
        "True Positives",
    ]
    for i, t in enumerate(ax.texts):
        t.set_text(t.get_text() + "\n" + cmlabels[i])
    plt.title("Matriz de Confusão", size=15)
    plt.xlabel("Predição", size=13)
    plt.ylabel("Realidade", size=13)

    # 2 -- Distributions of Predicted Probabilities of both classes
    df = pd.DataFrame({"probPos": pos_p, "target": y})
    plt.subplot(132)
    plt.hist(
        df[df.target == 1].probPos,
        density=True,
        bins=25,
        alpha=0.5,
        color="green",
        label=labels[0],
    )
    plt.hist(
        df[df.target == 0].probPos,
        density=True,
        bins=25,
        alpha=0.5,
        color="red",
        label=labels[1],
    )
    plt.axvline(0.5, color="blue", linestyle="--", label="Limiar(50%)")
    plt.xlim([0, 1])
    plt.title("Distribuição das Predições", size=15)
    plt.xlabel("Probabilidade (predição)", size=13)
    plt.ylabel("Amostras", size=13)
    plt.legend(loc="upper right")

    # 3 -- ROC curve with annotated decision point
    fp_rates, tp_rates, _ = roc_curve(y, p[:, 1])
    roc_auc = auc(fp_rates, tp_rates)
    plt.subplot(133)
    plt.plot(
        fp_rates,
        tp_rates,
        color="green",
        lw=1,
        label="ROC curve (area = %0.2f)" % roc_auc,
    )
    plt.plot([0, 1], [0, 1], lw=1, linestyle="--", color="grey")
    # plot current decision point:
    tn, fp, fn, tp = [i for i in cm.ravel()]
    plt.plot(fp / (fp + tn), tp / (tp + fn), "bo", markersize=8, label="Decision Point")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate", size=13)
    plt.ylabel("True Positive Rate", size=13)
    plt.title("ROC Curve", size=15)
    plt.legend(loc="lower right")
    plt.subplots_adjust(wspace=0.3)
    plt.tight_layout()
    plt.show()
    # Print and Return the F1 score
    tn, fp, fn, tp = [i for i in cm.ravel()]
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    F1 = 2 * (precision * recall) / (precision + recall)

    print(
        f"Precision: {round(precision, 2)} | "
        f"Recall: {round(recall, 2)} | "
        f"F1 Score: {round(F1, 2)} | "
        f"AUC Score: {round(roc_auc, 2)} | "
    )
    return F1
