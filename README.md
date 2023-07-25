# AWS Langchain
This repo provides a set of utility classes to work with [Langchain](https://github.com/hwchase17/langchain/tree/master). It currently has a retriever class `KendraIndexRetriever` for working with a Kendra index and sample scripts to execute the QA chain for SageMaker, Open AI and Anthropic providers.

## Setup Sagemaker Dev Environment (If using Sagemaker as IDE)
1. Go to Sagemaker Studio
2. Create new studio and user profile
3. Open Studio
4. Go to IAM->Role
5. Search for SageMakerExecutionRole
6. Add AmazonKendraReadOnlyAccess to the role

## Installing

Clone the repository
```bash
git clone https://github.com/aws-samples/amazon-kendra-langchain-extensions.git
```

Move to the repo dir
```bash
cd amazon-kendra-langchain-extensions
```


Install the classes
```bash
pip install .
```

## Usage

Usage with SageMaker Endpoint for Flan-T-XXL
```python
from aws_langchain.kendra_index_retriever import KendraIndexRetriever
from langchain.chains import RetrievalQA
from langchain import OpenAI
from langchain.prompts import PromptTemplate
from langchain import SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import ContentHandlerBase
import json

class ContentHandler(ContentHandlerBase):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
        input_str = json.dumps({"inputs": prompt, "parameters": model_kwargs})
        return input_str.encode('utf-8')

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json[0]["generated_text"]

content_handler = ContentHandler()
llm=SagemakerEndpoint(
        endpoint_name=endpoint_name,
        region_name="us-east-1", 
        model_kwargs={"temperature":1e-10, "max_length": 500},
        content_handler=content_handler
    )

retriever = KendraIndexRetriever(kendraindex=kendra_index_id,
        awsregion=region,
        return_source_documents=True
    )

prompt_template = """
The following is a friendly conversation between a human and an AI.
The AI is talkative and provides lots of specific details from its context.
If the AI does not know the answer to a question, it truthfully says it
does not know.
{context}
Instruction: Based on the above documents, provide a detailed answer for, {question} Answer "don't know" if not present in the document. Solution:
"""
PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)
chain_type_kwargs = {"prompt": PROMPT}
qa = RetrievalQA.from_chain_type(
    llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs=chain_type_kwargs,
    return_source_documents=True
)
result = qa("What's SageMaker?")
print(result['answer'])

```

## Creating an Amazon Kendra index with test data
If you wish to create a sample Kendra index and index sample data and experiment with the index using the sample applications you can deploy the CloudFormation template samples/kendra-docs-index.yaml


## Running samples
For executing sample chains, install the optional dependencies
```bash
pip install ".[samples]"
```

Ensure that the environment variables are set for the aws region, kendra index id and the provider/model used by the sample.
For example, for running the `kendra_chat_flan_xl.py` sample, these environment variables must be set: AWS_REGION, KENDRA_INDEX_ID
and FLAN_XL_ENDPOINT.
You can use commands as below to set the environment variables.
```bash
export AWS_REGION="<YOUR-AWS-REGION>"
export KENDRA_INDEX_ID="<YOUR-KENDRA-INDEX-ID>"
export FALCON_ENDPOINT="<YOUR-SAGEMAKER-ENDPOINT-FOR-FALCON>"
export ANTHROPIC_API_KEY="<YOUR-ANTHROPIC-API-KEY>"
export BEDROCK_ENDPOINT_URL="<YOUR-BEDROCK-ENDPOINT-URL>"
```

### Running samples from the streamlit app
The samples directory is bundled with an `app.py` file that can be run as a web app using streamlit. 
```bash
cd samples
streamlit run app.py falcon
```
The above command will run the `kendra_chat_falcon` as the LLM chain. In order to run a different chain, pass a different provider, for example for running the `anthropic` chain run this command `streamlit run app.py anthropic`.

### If using Bedrock as LLM model

Update boto3 SDK with preview bedrock preview features by downloading the following scripts in this folder

```sh
bash download-dependencies.sh
```

To install it, run the following commands:

```python
pip install dependencies/botocore-1.29.162-py3-none-any.whl 
pip install dependencies/boto3-1.26.162-py3-none-any.whl 
pip install dependencies/awscli-1.27.162-py3-none-any.whl 
```

### Running samples from the command line
```bash
python samples/<sample-file-name.py>
```

## Uninstall
```bash
pip uninstall aws-langchain
```

## Contributing
Create your GitHub branch and make a pull request.
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

Install in editable mode, this will make sure your changes are synced in local python env
```bash
pip install -e ".[dev]"
```

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

