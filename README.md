# Deploy Docker - Machine Learning Model Deployment with Azure Batch

## Introduction

This project demonstrates how to deploy a machine learning model using Docker containers and Azure Batch. The setup leverages Azure's scalable cloud resources to manage and execute Dockerized workloads efficiently. This is particularly useful for deploying models that require heavy computation, ensuring scalability and reliability.

## Prerequisites

Before starting, ensure you have the following:

- **Azure Account**: You'll need an active Azure subscription.
- **Docker**: Install Docker on your local machine [here](https://docs.docker.com/get-docker/).
- **Azure CLI**: The Azure Command-Line Interface (CLI) is necessary for interacting with Azure services. Install it from [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).
Or type `pip install azure-cli` on your terminal.
- **Git**: Version control tool to clone this repository.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/jotap123/deploy-docker.git
cd deploy-docker
```

### 2. Configure Azure

- **Login to Azure**:

    ```bash
    az login
    ```

- **Set up Azure Batch Account**: Create a batch account and pool following the instructions in the Azure documentation [here](https://docs.microsoft.com/en-us/azure/batch/). Or create it via Terraform following the scripts on the "tf" folder.

### 3. Docker Setup

- **Build Docker Image**:

    Navigate to the directory containing the Dockerfile and build the Docker image:

    ```bash
    docker build -t my-ml-model .
    ```

## Deployment Instructions

### 1. Create a Docker Container on Azure

Upload your Docker image to Azure Container Registry (ACR) or use Docker Hub, and then configure your Batch Pool to use this image.

### 2. Submit Batch Job

- **Submit a Job**: Define your task and submit it to the Azure Batch pool. You can use the provided script or manually submit via the Azure portal.

### 3. Monitor and Manage

- **Monitor Jobs**: Use the Azure portal or CLI to monitor job progress, logs, and outputs.

## Usage

Once deployed, you can interact with your machine learning model by submitting tasks to the Azure Batch pool. The output and logs can be retrieved from Azure Storage or directly from the Batch interface.

## Troubleshooting

- **Docker Build Errors**: Ensure your Dockerfile is correctly configured and all dependencies are installed.
- **Azure Authentication Issues**: Make sure you are logged in to Azure CLI and have the necessary permissions.
- **Job Failures**: Check the logs for errors in the task execution.

## Contributing

Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request with your changes. Ensure your code follows the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.