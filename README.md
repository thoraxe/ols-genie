# Project Genie PoC

* clone the llama-stack server repo https://github.com/meta-llama/llama-stack
* grab version v0.1.9 of the server repo
* set up your initial python venv for this project (i use the same for llama stack)
* in the llama stack server repo folder: 
   
    pip install -e --upgrade .

* in this folder:
		pip install -r requirements.txt
		pip install uv

* build the llama stack server into the venv

    UV_PYTHON=$(which python) llama stack build --config llama-stack-build.yaml --image-type venv --image-name=openai

* run the llama stack server with required env vars

    llama stack run llama-stack-run.yaml --image-type venv --env OPENAI_API_KEY=xxxx

* get your api token for your openshift environment
* get the url for the prometheus server for your openshift environment

* run this project's fastapi stuff

    PROMETHEUS_URL=xx PROMETHEUS_TOKEN=xx LLAMA_HOST=localhost LLAMA_PORT=8231 fastapi main.py