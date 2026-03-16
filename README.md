# ai|coustics API Examples

> [!WARNING]
> This API has been sunset. Please migrate to the SDK: https://docs.ai-coustics.com/

Welcome to the ai|coustics API Python Examples repository! This repository contains example scripts and tutorials on how to use the ai|coustics API with Python.

## Overview

ai|coustics provides AI-driven speech enhancement to enriching media experiences and natural conversations. This repository provides sample code to help you quickly integrate the ai|coustics API into your Python applications.

## Getting Started

### Prerequisites

- Python 3.12.4
- An ai|coustics API key. You can get one by signing up on our [developer portal](https://developers.ai-coustics.io/signup).

### Installation

1. Clone the repository:

```bash
git clone https://github.com/ai-coustics/api-tutorials.git
cd api-tutorials
```

2. Create a virtual environment, activate it, and install the dependencies:
    - Recommended: using the `uv` ([documentation](https://docs.astral.sh/uv/)). Run `uv sync`
    - Or by using the python `venv` module and the `requirements.txt` file

3. Create the `.env` file that would include `API_KEY` and optionally the `WEBHOOK_SIGNATURE` values. Check the description of the environment values at the [configs.py](./src/configs.py)

### Usage

The [upload.py](./src/examples/upload.py) and [download.py](/src/examples/download.py) are simple examples. The [advanced.py](./src/examples/advanced.py) is implementing the whole cycle: uploading, catching an update using webhook, and downloading an enhanced media file.

Every example file has the entry point in the bottom where you can set your values. For instance in the [download.py](/src/examples/download.py#L48) you are required to set the `generated_name` variable value, as a generated name of a file is unique.

#### Simple examples

1. Upload
```sh
python -m src.examples.upload
```

2. Download
```sh
python -m src.examples.download
```
Don't forget to change the `generated_name`, using the value returned from the upload example.

#### Advanced example

```sh
python -m src.examples.advanced
```
1. Expose the `localhost:8002` adress to the internent. There are multiple options of how you can do this, but for testing you can consider such free services like [ngrok](https://ngrok.com/docs/getting-started/). Optionally, at the [entry point](./src/examples/advanced.py#L227) you can change the default values of the `webhook_server_host` and `webhook_server_port` variables, which are `"localhost"` and `8002` respectively.
2. Create a webhook on the [developer portal](https://developers.ai-coustics.io/webhooks). The `URL` should be routing to the `<exposed_address>/callbacks`, as the advacned script is listening for the `http://localhost:8002/callbacks` endpoint. If you configured the `WEBHOOK_SIGNATURE` environment variable, use it as the `Signature` value. 

To better understand where media files are comming from, review the [mocks.py](./src/mocks.py) file and change the [mock_get_media_queue_period](./src/examples/advanced.py#L231) variable's value.

### Documentation

You can find the full API documentation [here](https://developers.ai-coustics.io/documentation).

### License

This project is licensed under the [MIT License](https://github.com/ai-coustics/api-tutorials/blob/main/LICENSE).

### Contact
For any questions, feel free to reach out to us at [support@ai-coustics.com](mailto:support@ai-coustics.com) or visit our website [ai-coustics.com](https://ai-coustics.com).
