from dags.visualization.inference import predictions


def run_dag(task):
    from dags.runner import run_task

    run_task(task)


def predict():
    predictions()


if __name__ == "__main__":
    predict()
