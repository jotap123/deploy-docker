import os

import docker
import dotenv
import tomli

dotenv.load_dotenv()


def build_image():
    with open("pyproject.toml", "rb") as file:
        toml_data = tomli.load(file)

    acr_name = "54e5ef7c9fb5461ba8e5bfdfb25ddb7d"
    project_tag = toml_data["project"]["version"]
    tag = f"{acr_name}.azurecr.io/test:{project_tag}"

    # Get the ACR login server and username/password
    acr_login_server = f"{acr_name}.azurecr.io"
    acr_username = os.environ["AZURE_CLIENT_ID"]
    acr_password = os.environ["AZURE_CLIENT_SECRET"]

    client = docker.from_env()
    client.login(
        username=acr_username, password=acr_password, registry=acr_login_server
    )
    image, logs = client.images.build(path=".", tag=tag)
    for line in client.images.push(tag, stream=True):
        print(line)


if __name__ == "__main__":
    build_image()
