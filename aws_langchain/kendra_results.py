from langchain.docstore.document import Document
import boto3
import re
import os

def clean_result(res_text):
    res = re.sub("\s+", " ", res_text).replace("...","")
    return res
    
def get_top_n_results(resp, count):
    r = resp["ResultItems"][count]
    doc_title = r["DocumentTitle"] #for Query API -> use: r["DocumentTitle"]["Text"]
    doc_uri = r["DocumentURI"]
    r_type = "Passage"  #for Query API -> use: r["Type"]

    #for Query API
    # if (r["AdditionalAttributes"] and r["AdditionalAttributes"][0]["Key"] == "AnswerText"):
    #     res_text = r["AdditionalAttributes"][0]["Value"]["TextWithHighlightsValue"]["Text"]
    # else:
    #     res_text = r["DocumentExcerpt"]["Text"]

    res_text = r["Content"]
    
    doc_excerpt = clean_result(res_text)
    combined_text = "Document Title: " + doc_title + "\nDocument Excerpt: \n" + doc_excerpt + "\n"

    print("combined")
    print(combined_text)

    return {"page_content":combined_text, "metadata":{"source":doc_uri, "title": doc_title, "excerpt": doc_excerpt, "type": r_type}}

def kendra_query(kclient, kquery, kcount, kindex_id):

    

    # response = kclient.query(IndexId=kindex_id, QueryText=kquery.strip())
    # response = kclient.query(IndexId=kindex_id, QueryText=kquery.strip(), AttributeFilter = {'AndAllFilters': 
    #         [ 
    #             {"EqualsTo": {"Key": "_data_source_id","Value": {"StringValue": "e81b3506-609c-4187-8cae-24deee6a0edd"}}},
    #         ]
    #         }
    #     ])
    #bdf1c363-d945-4c36-8b9d-808441f64ba1
    #Thoughtworks: 43f7fdc3-9963-4934-bd3d-2e16697145de

    if "KENDRA_DATASOURCE" in os.environ:
        datasource = os.environ["KENDRA_DATASOURCE"]
        if datasource == "":
            response = kclient.retrieve(IndexId=kindex_id, QueryText=kquery.strip())
        else:
            response=kclient.retrieve(
                QueryText = kquery.strip(),
                IndexId = kindex_id,
                AttributeFilter = {'AndAllFilters': 
                    [ 
                        {"EqualsTo": {"Key": "_data_source_id","Value": {"StringValue": datasource}}},
                    ]
                }
            )
    else:
        response = kclient.retrieve(IndexId=kindex_id, QueryText=kquery.strip())
        
    if len(response["ResultItems"]) > kcount:
        r_count = kcount
    else:
        r_count = len(response["ResultItems"])
        
    docs = [get_top_n_results(response, i) for i in range(0, r_count)]
    return [Document(page_content = d["page_content"], metadata = d["metadata"]) for d in docs]

def kendra_client(kindex_id, kregion):
    kclient = boto3.client('kendra', region_name=kregion)
    return kclient
