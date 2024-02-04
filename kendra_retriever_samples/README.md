# AWS Langchain
This repo provides a set of samples to work with [Langchain](https://github.com/hwchase17/langchain/tree/master) and Amazon Kendra. It currently has samples for working with a [Kendra retriever class](https://python.langchain.com/docs/modules/data_connection/retrievers/integrations/amazon_kendra_retriever) to execute a QA chain for SageMaker, Open AI and Anthropic providers. 

## Installing

Clone the repository
```bash
git clone https://github.com/aws-samples/amazon-kendra-langchain-extensions.git
```

Move to the repo dir
```bash
cd amazon-kendra-langchain-extensions
```

Move to the samples dir
```bash
cd kendra_retriever_samples
```

Install the dependencies

If you are using pip
```bash
pip install -r requirements.txt
```

If you are using Conda
```bash
conda env create -f environment.yml 
```

### For Bedrock
If you are using Bedrock, make sure that you update to the latest boto3 and langchain version with bedrock support and you use an AWS_PROFILE  that has access to bedrock.

```
pip install --force-reinstall "langchain>=0.0.306"
pip install --force-reinstall "boto3>=1.28.57"
```

## Running samples
Before you run the sample, you need to deploy a Large Language Model (or get an API key if you using Anthropic or OPENAI). The samples in this repository have been tested on models deployed using SageMaker Jumpstart.  The model id for the LLMS are specified in the table below.

With the latest sagemaker release each endpoint can hold multiple models (called InferenceComponent). For jumpstart models, optionally specify the INFERENCE_COMPONENT_NAME as well as an environment varialbe


| Model name | env var name | Endpoint Name | Inference component name (optional) |streamlit provider name |
| -----------| -------- | ------------------ |  ----------------- |
| Falcon 40B instruct | FALCON_40B_ENDPOINT, INFERENCE_COMPONENT_NAME | <Endpoint_name> | <Inference_component_name>|falcon40b |
| Llama2 70B instruct | LLAMA_2_ENDPOINT, INFERENCE_COMPONENT_NAME |<Endpoint_name> | <Inference_component_name> | llama2 |
| Bedrock Titan | None | | | bedrock_titan|
| Bedrock Claude | None | | | bedrock_claude|
| Bedrock Claude V2 | None | | | bedrock_claudev2|


after deploying the LLM, set up environment variables for kendra id, aws_region endpoint name (or the API key for an external provider) and optionally the inference component name

For example, for running the `kendra_chat_llama_2.py` sample, these environment variables must be set: AWS_REGION, KENDRA_INDEX_ID,  LLAMA_2_ENDPOINT and INFERENCE_COMPONENT_NAME.  INFERENCE_COMPONENT_NAME is only required when deploying the jumpstart through the console or if you explicitely create an inference component using code. It is also possible to create an endpoint without and inference component in which case, do not set the INFERENCE_COMPONENT_FIELD.  

You can use commands as below to set the environment variables. Only set the environment variable for the provider that you are using. For example, if you are using Flan-xl only set the FLAN_XXL_ENDPOINT. There is no need to set the other Endpoints and keys. 

```bash
export AWS_REGION=<YOUR-AWS-REGION>
export AWS_PROFILE=<AWS Profile>
export KENDRA_INDEX_ID=<YOUR-KENDRA-INDEX-ID>

export FALCON_40B_ENDPOINT=<YOUR-SAGEMAKER-ENDPOINT-FOR-FALCON> # only if you are using falcon as the endpoint
export LLAMA_2_ENDPOINT=<YOUR-SAGEMAKER-ENDPOINT-FOR-LLAMA2> #only if you are using llama2 as the endpoint
export INFERENCE_COMPONENT_NAME=<YOUR-SAGEMAKER-INFERENCE-COMPONENT-NAME> # if you are deploying the FM via the JumpStart console.

export OPENAI_API_KEY=<YOUR-OPEN-AI-API-KEY> #  only if you are using OPENAI as the endpoint
export ANTHROPIC_API_KEY=<YOUR-ANTHROPIC-API-KEY> #  only if you are using Anthropic as the endpoint
```


### Running samples from the streamlit app
The samples directory is bundled with an `app.py` file that can be run as a web app using streamlit. 

```bash
streamlit run app.py llama2
```

The above command will run the `kendra_chat_llama_2` as the LLM chain. In order to run a different chain, pass a different provider, for example for running the `open_ai` chain run this command `streamlit run app.py openai`. Use the column 'streamlit provider name' from the table above to find out the provider name



### Running samples from the command line
```bash
python <sample-file-name.py>
```

## Contributing
Create your fork and submit your changes via a pull request.
See [CONTRIBUTING](../CONTRIBUTING.md) for more information.

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

