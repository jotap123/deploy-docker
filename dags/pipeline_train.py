from dags.models.train import train_model


def run_dag(task):
    from dags.runner import run_task

    run_task(task)


def train():
    train_model()


if __name__ == "__main__":
    train()
