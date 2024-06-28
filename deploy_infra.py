import datetime
import os
import time

import crontab
import dotenv
import tomli
from azure.batch import BatchServiceClient
from azure.batch.models import (
    AutoUserScope,
    AutoUserSpecification,
    BatchErrorException,
    CloudServiceConfiguration,
    ContainerRegistry,
    ElevationLevel,
    EnvironmentSetting,
    JobAddParameter,
    JobConstraints,
    JobManagerTask,
    PoolAddParameter,
    PoolInformation,
    TaskAddParameter,
    TaskContainerSettings,
    TaskDependencies,
    UserIdentity,
)
from azure.common.credentials import ServicePrincipalCredentials

APP_NAME = "test"
pool_id = "batchpool"


def _get_batch_client():
    dotenv.load_dotenv()
    # authenticate to Azure API using an administrative service principal
    # (ie. Jenkins) and get batch client. We expect the standard `AZURE_` env variables
    # to be present (can be part of the local .env file)
    batch_url = "https://mlopaesbatch.eastus2.batch.azure.com"
    credentials = ServicePrincipalCredentials(
        client_id=os.environ["AZURE_CLIENT_ID"],
        secret=os.environ["AZURE_CLIENT_SECRET"],
        tenant=os.environ["AZURE_TENANT_ID"],
        resource="https://batch.core.windows.net/",
    )
    batch_client = BatchServiceClient(credentials, batch_url=batch_url)
    return batch_client


def _get_container_settings(version):
    acr_name = "54e5ef7c9fb5461ba8e5bfdfb25ddb7d"
    server = f"{acr_name}.azurecr.io"
    image_tag = f"{server}/{APP_NAME}:{version}"

    # setup container info for tasks
    container_settings = TaskContainerSettings(
        image_name=image_tag,
        registry=ContainerRegistry(
            registry_server=server,
            user_name=os.environ["AZURE_CLIENT_ID"],
            password=os.environ["AZURE_CLIENT_SECRET"],
        ),
        working_directory="containerImageDefault",
    )
    return container_settings


def _get_env_settings():
    batch_env = {
        "AZURE_CLIENT_ID": os.environ["AZURE_CLIENT_ID"],
        "AZURE_CLIENT_SECRET": os.environ["AZURE_CLIENT_SECRET"],
        "AZURE_TENANT_ID": os.environ["AZURE_TENANT_ID"],
    }

    environment_settings = [
        EnvironmentSetting(name=name, value=value) for name, value in batch_env.items()
    ]

    return environment_settings


def _get_job_manager_task(version):
    environment_settings = _get_env_settings()

    command = "echo 'Running Container'"
    job_manager_task = JobManagerTask(
        id="mlops-manager-task",
        display_name="MLOps Job Manager Task",
        command_line=command,
        container_settings=_get_container_settings(version),
        environment_settings=environment_settings,
        kill_job_on_completion=False,
    )

    return job_manager_task


def create_batch_pool(batch_client):
    pool = batch_client.pool.add(
        PoolAddParameter(
            id=pool_id,
            vm_size="Standard_D2_v3",
            cloud_service_configuration=CloudServiceConfiguration(os_family="5"),
            target_dedicated_nodes=1,
        )
    )
    return pool


def _add_job(batch_client: BatchServiceClient, job_id, job_manager_task):
    try:
        batch_client.job.get(job_id)
        batch_client.job.delete(job_id)
        time.sleep(30)

        print(f"Recreating job {job_id}")
        job = JobAddParameter(
            id=job_id,
            pool_info=PoolInformation(pool_id=pool_id),
            uses_task_dependencies=True,
            job_manager_task=job_manager_task,
            constraints=JobConstraints(
                max_wall_clock_time="PT18H", max_task_retry_count=1
            ),
        )
        batch_client.job.add(job)
    except BatchErrorException as e:
        print(f"{e.error.code}")
        print(f"Adding job {job_id}")
        job = JobAddParameter(
            id=job_id,
            pool_info=PoolInformation(pool_id=pool_id),
            uses_task_dependencies=True,
            job_manager_task=job_manager_task,
            constraints=JobConstraints(
                max_wall_clock_time="PT18H", max_task_retry_count=1
            ),
        )
        batch_client.job.add(job)


def _parse_cron(cron, tz):
    now = datetime.datetime.now(tz=tz)
    ct = crontab.CronTab(cron)
    _next = ct.next(now=now, default_utc=False, delta=False)
    _next = datetime.datetime.fromtimestamp(_next, tz=tz)
    _next2 = ct.next(now=_next, default_utc=False, delta=False)
    _next2 = datetime.datetime.fromtimestamp(_next2, tz=tz)
    recurrence = _next2 - _next
    start_time = _next
    return start_time, recurrence


def _add_tasks(
    job_id: str, dag: str, spec: dict, version: str, batch_client: BatchServiceClient
):
    dag_tasks = spec["tasks"]
    environment_settings = _get_env_settings()

    user = AutoUserSpecification(
        scope=AutoUserScope.task,
        elevation_level=ElevationLevel.admin,
    )

    # add tasks
    for i, task_name in enumerate(dag_tasks):
        task_id = f"{task_name}"
        command = f"'python run.py task {dag} {task_name}'"
        depends_on = TaskDependencies(task_ids=[dag_tasks[i - 1]]) if i > 0 else None
        # source_file_pattern = ".*"
        # container_url = "https://testmlopaes.dfs.core.windows.net/logs/"
        # output_path = f"{dag}/{job_id}/{task_id}"
        task = TaskAddParameter(
            id=task_id,
            display_name=f"Test Task {task_name}",
            command_line=command,
            container_settings=_get_container_settings(version=version),
            environment_settings=environment_settings,
            depends_on=depends_on,
            user_identity=UserIdentity(auto_user=user),
            # output_files=[
            #     OutputFile(
            #         file_pattern=source_file_pattern,
            #         destination=OutputFileDestination(
            #             container=OutputFileBlobContainerDestination(
            #                 container_url=container_url, path=output_path
            #             ),
            #         ),
            #         upload_options=OutputFileUploadOptions(
            #             upload_condition="taskCompletion"
            #         ),
            #     )
            # ],
        )
        print(f"Adding task: {task_id}")
        batch_client.task.add(job_id, task)


def run_job():
    import run

    batch_client = _get_batch_client()
    with open("pyproject.toml", "rb") as file:
        toml_data = tomli.load(file)

    specs = run.get_dags()
    specs.pop("config")
    dags = specs.keys()
    version = toml_data["project"]["version"]

    for dag in dags:
        spec = specs[dag]

        job_manager_task = _get_job_manager_task(version)

        job_id = f"test-{dag}"

        _add_job(batch_client, job_id, job_manager_task)
        _add_tasks(job_id, dag, spec, version, batch_client)


if __name__ == "__main__":
    run_job()
