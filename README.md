# ai|coustics API Examples

Welcome to the ai|coustics API Python Examples repository! This repository contains example scripts and tutorials on how to use the ai|coustics API with Python.

## Overview

ai|coustics provides AI-driven speech enhancement to enriching media experiences and natural conversations. This repository provides sample code to help you quickly integrate the ai|coustics API into your Python applications.

## Getting Started

### Prerequisites

- Python 3.10+
- An ai|coustics API key. You can get one by signing up on our [developer portal](https://developers.ai-coustics.com/signup).

### Installation & Usage

1. Clone the repository:

```bash
git clone https://github.com/ai-coustics/api-tutorials.git
cd api-tutorials
```

2. Create a virtual environment, activate it, and install the dependencies:
    - Recommended: using the `poetry` ([documentation](https://python-poetry.org/docs/))
    - Or by using the python `venv` module and the `requirements.txt` file

3. Create the `.env` file that would include `API_KEY` and optionally the `WEBHOOK_SIGNATURE` values. Check the description of the environment values at the [configs.py](./src/configs.py)

4. Review and run the examples. The [upload.py](./src/examples/upload.py) and [download.py](/src/examples/download.py) are simple examples. The [advanced.py](./src/examples/advanced.py) is implementing the whole cycle: uploading, catching an update using webhook, and downloading an enhanced media file.

#### How to run the examples:
1. The `.env` file has required `API_KEY` and optional `WEBHOOK_SIGNATURE` variables values.
2. Every example file has the entry point in the bottom where you can set your values. For instance in the [download.py](/src/examples/download.py#L48) you are required to set the `generated_name` variable value, as a generated name of a file is unique.

**Advanced example:** since the [advanced.py](./src/examples/advanced.py) is using the webhook, you should consider following:
- The address of a server, that is started when you run the [advanced.py](./src/examples/advanced.py) script, shold be made accessible on the internet. There are multimple options of how you can do this, but for testing you can consider such free services like [ngrok](https://ngrok.com/docs/getting-started/). Such services let you expose your local address on the internet easily. 
- At the [entry point](./src/examples/advanced.py#L227) you can change the default values of the `webhook_server_host` and `webhook_server_port` variables, which are `"localhost"` and `8002` respectively.
- To better understand where media files are comming from, review the [mocks.py](./src/mocks.py) file and change the [mock_get_media_queue_period](./src/examples/advanced.py#L231) variable's value.

### Documentation

You can find the full API documentation [here](https://developers.ai-coustics.com/documentation).

### License

This project is licensed under the [MIT License](https://github.com/ai-coustics/api-tutorials/blob/main/LICENSE).

### Contact
For any questions, feel free to reach out to us at [support@ai-coustics.com](mailto:support@ai-coustics.com) or visit our website [ai-coustics.com](https://ai-coustics.com).