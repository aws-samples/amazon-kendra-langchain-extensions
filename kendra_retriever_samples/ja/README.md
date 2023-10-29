# AWS Langchain
このリポジトリは [Langchain](https://github.com/hwchase17/langchain/tree/master) と Amazon Kendra を利用するためのサンプルを提供します。
現在、SageMaker、OpenAI、および Anthropic プロバイダー向けに QA チェーンを実行するための [Kendra retriever クラス](https://python.langchain.com/docs/modules/data_connection/retrievers/integrations/amazon_kendra_retriever)のサンプルが含まれています。

## インストール

リポジトリをクローンします
```bash
git clone https://github.com/aws-samples/amazon-kendra-langchain-extensions.git
```

リポジトリのあるディレクトリに移動します
```bash
cd amazon-kendra-langchain-extensions
```

サンプルディレクトリに移動します
```bash
cd kendra_retriever_samples
```

依存関係をインストールします

pip を使用する場合
```bash
pip install -r requirements.txt
```

Conda を利用する場合
```bash
conda env create -f environment.yml
```

### Bedrock の場合
Bedrock を使用する場合、Bedrock サポートを持つ最新の boto3 および langchain バージョンに更新し、Bedrock へのアクセス権を持つ AWS_PROFILE を使用していることを確認してください。

```
pip install --force-reinstall "langchain>=0.0.306"
pip install --force-reinstall "boto3>=1.28.57"
```

## サンプルの実行
サンプルを実行する前に、Large Language Model をデプロイする（または Anthropic や OpenAI を使用する場合は API キーを取得する）必要があります。このリポジトリのサンプルは、SageMaker Jumpstart を使用して展開されたモデルでテストされています。 LLM のモデル ID は以下の表にまとめられています。

| モデル名            | 環境変数名          | Jumpstart モデル ID                      | streamlit プロバイダ | 日本語対応 |
| ------------------- | ------------------- | ---------------------------------------- | -------------------- | ---------- |
| Flan XL             | FLAN_XL_ENDPOINT    | huggingface-text2text-flan-t5-xl         | flanxl               | No         |
| Flan XXL            | FLAN_XXL_ENDPOINT   | huggingface-text2text-flan-t5-xxl        | flanxxl              | No         |
| Falcon 40B instruct | FALCON_40B_ENDPOINT | huggingface-llm-falcon-40b-instruct-bf16 | falcon40b            | Yes        |
| Llama2 70B instruct | LLAMA_2_ENDPOINT    | meta-textgeneration-llama-2-70b-f        | llama2               | No         |
| Bedrock Titan       | None                |                                          | bedrock_titan        | No         |
| Bedrock Claude      | None                |                                          | bedrock_claude       | Yes        |
| Bedrock Claude V2   | None                |                                          | bedrock_claudev2     | Yes        |

LLMをデプロイした後、kendra ID、aws_region、エンドポイント名（または外部プロバイダーの API キー）の環境変数を設定する必要があります。

例えば、`kendra_chat_llama_2.py` のサンプルを実行する場合、以下の環境変数を設定する必要があります
- AWS_REGION
- KENDRA_INDEX_ID
- LLAMA_2_ENDPOINT

以下のコマンドを使用して環境変数を設定できます。使用するプロバイダーの環境変数のみを設定します。たとえば、Flan-xl を使用する場合は FLAN_XXL_ENDPOINT のみを設定します。他のエンドポイントとキーは設定する必要はありません。

```bash
export LANGUAGE_CODE=ja
export AWS_REGION=<YOUR-AWS-REGION>
export AWS_PROFILE=<AWS Profile>
export KENDRA_INDEX_ID=<YOUR-KENDRA-INDEX-ID>

export FLAN_XL_ENDPOINT=<YOUR-SAGEMAKER-ENDPOINT-FOR-FLAN-T-XL> # only if you are using FLAN_XL
export FLAN_XXL_ENDPOINT=<YOUR-SAGEMAKER-ENDPOINT-FOR-FLAN-T-XXL> # only if you are using FLAN_XXL
export FALCON_40B_ENDPOINT=<YOUR-SAGEMAKER-ENDPOINT-FOR-FALCON> # only if you are using falcon as the endpoint
export LLAMA_2_ENDPOINT=<YOUR-SAGEMAKER-ENDPOINT-FOR-LLAMA2> #only if you are using llama2 as the endpoint

export OPENAI_API_KEY=<YOUR-OPEN-AI-API-KEY> #  only if you are using OPENAI as the endpoint
export ANTHROPIC_API_KEY=<YOUR-ANTHROPIC-API-KEY> #  only if you are using Anthropic as the endpoint
```


### streamlit アプリからのサンプルの実行（日本語未対応）
サンプルディレクトリには、streamlit を使用してウェブアプリとして実行できる `app.py` ファイルが含まれています。

```bash
streamlit run app.py llama2
```

上記のコマンドは、LLM チェーンとして `kendra_chat_llama_2` を実行します。異なるチェーンを実行するには、異なるプロバイダーを渡してください。たとえば、`open_ai` チェーンを実行する場合は `streamlit run app.py openai` を実行します。テーブル上の「streamlitプロバイダ名」列を活用してプロバイダ名を確認してください。

### コマンドラインからのサンプルの実行
```bash
python <sample-file-name.py>
```

## Contributing
このリポジトリのフォークを作成して、変更内容をプルリクエストで提出してください。
詳細については、[CONTRIBUTING](../CONTRIBUTING.md) を参照してください。

## License
このライブラリは MIT-0 ライセンスのもとで提供されています。詳細は LICENSE ファイルをご覧ください。
