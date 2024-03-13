# LLaMa.cpp Gemma Web-UI
This project uses llama.cpp to load model from a local file, delivering fast and memory-efficient inference.  
The project is currently designed for Google Gemma, and will support more models in the future.

## Deployment
### Prerequisites

- Download Gemma model from Google repository (https://huggingface.co/google/gemma-2b-it).

- Quantize the Gemma model (highly recommended if target machine has limited memory).  
### Installation

1. Download Gemma model from Google repository.
2. Edit the model-path config.yaml, this should point to the actual model path.
3. Start the web-ui by command:
    ``` bash
    screen -S "webui" bash ./start-ui.sh
    ```
