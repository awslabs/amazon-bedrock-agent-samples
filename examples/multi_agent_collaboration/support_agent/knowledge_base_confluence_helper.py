# Copyright 2024 Amazon.com and its affiliates; all rights reserved.
# This file is AWS Content and may not be duplicated or distributed without permission

"""
This module contains a helper class for building and using Knowledge Bases for Amazon Bedrock.
The KnowledgeBasesForAmazonBedrock class provides a convenient interface for working with Knowledge Bases.
It includes methods for creating, updating, and invoking Knowledge Bases, as well as managing
IAM roles and OpenSearch Serverless.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError
from opensearchpy import (
    OpenSearch,
    RequestsHttpConnection,
    AWSV4SignerAuth,
    RequestError,
)
import pprint
from retrying import retry
import random

valid_embedding_models = [
    "cohere.embed-multilingual-v3",
    "cohere.embed-english-v3",
    "amazon.titan-embed-text-v1",
    "amazon.titan-embed-text-v2:0",
]
pp = pprint.PrettyPrinter(indent=2)


def interactive_sleep(seconds: int):
    
    """
    Support functionality to induce an artificial 'sleep' to the code in order to wait for resources to be available
    Args:
        seconds (int): number of seconds to sleep for
    """
    dots = ""
    for i in range(seconds):
        dots += "."
        print(dots, end="\r")
        time.sleep(1)


class ConfluenceKnowledgeBasesForAmazonBedrock:
    """
    Support class that allows for:
        - creation (or retrieval) of a Knowledge Base for Amazon Bedrock with all its pre-requisites
          (including OSS, IAM roles and Permissions and S3 bucket)
        - Ingestion of data into the Knowledge Base
        - Deletion of all resources created
    """

    def __init__(self, suffix=None):
        """
        Class initializer
        """
        boto3_session = boto3.session.Session()
        self.region_name = boto3_session.region_name
        self.iam_client = boto3_session.client("iam", region_name=self.region_name)
        self.account_number = (
            boto3.client("sts", region_name=self.region_name)
            .get_caller_identity()
            .get("Account")
        )
        self.suffix = random.randrange(100, 900)
        self.identity = boto3.client(
            "sts", region_name=self.region_name
        ).get_caller_identity()["Arn"]
        self.aoss_client = boto3_session.client(
            "opensearchserverless", region_name=self.region_name
        )
        self.s3_client = boto3.client("s3", region_name=self.region_name)
        self.bedrock_agent_client = boto3.client(
            "bedrock-agent", region_name=self.region_name
        )
        self.bedrock_agent_client = boto3.client(
            "bedrock-agent", region_name=self.region_name
        )
        credentials = boto3.Session().get_credentials()
        self.awsauth = AWSV4SignerAuth(credentials, self.region_name, "aoss")
        self.oss_client = None
        self.data_bucket_name = None
    
    

    def create_or_retrieve_confluence_knowledge_base(
        self,
        kb_name: str,
        kb_description: str = None,
        confluence_url: str = None,
        embedding_model: str = "amazon.titan-embed-text-v2:0",
        secret_arn: str = None,

    ):
        """
        Function used to create a new Knowledge Base using Confluence as data source or retrieve an existent one

        Args:
            kb_name: Knowledge Base Name
            kb_description: Knowledge Base Description
            confluence_url: Confluence URL (e.g., https://your-domain.atlassian.net)
            embedding_model: Name of Embedding model to be used on Knowledge Base creation

        Returns:
            kb_id: str - Knowledge base id
            ds_id: str - Data Source id
        """
        kb_id = None
        ds_id = None
        
        # Check if KB already exists
        kbs_available = self.bedrock_agent_client.list_knowledge_bases(
            maxResults=100,
        )
        for kb in kbs_available["knowledgeBaseSummaries"]:
            if kb_name == kb["name"]:
                kb_id = kb["knowledgeBaseId"]
                
        if kb_id is not None:
            # If KB exists, get the data source ID
            ds_available = self.bedrock_agent_client.list_data_sources(
                knowledgeBaseId=kb_id,
                maxResults=100,
            )
            for ds in ds_available["dataSourceSummaries"]:
                if kb_id == ds["knowledgeBaseId"]:
                    ds_id = ds["dataSourceId"]
            print(f"Knowledge Base {kb_name} already exists.")
            print(f"Retrieved Knowledge Base Id: {kb_id}")
            print(f"Retrieved Data Source Id: {ds_id}")
        else:
            print(f"Creating KB {kb_name}")
            
            # Validate embedding model
            if embedding_model not in valid_embedding_models:
                valid_embeddings_str = str(valid_embedding_models)
                raise ValueError(
                    f"Invalid embedding model. Your embedding model should be one of {valid_embeddings_str}"
                )

            # Create policy and role names
            encryption_policy_name = f"{kb_name}-sp-{self.suffix}"
            network_policy_name = f"{kb_name}-np-{self.suffix}"
            access_policy_name = f"{kb_name}-ap-{self.suffix}"
            kb_execution_role_name = f"AmazonBedrockExecutionRoleForKnowledgeBase_{self.suffix}"
            fm_policy_name = f"AmazonBedrockFoundationModelPolicyForKnowledgeBase_{self.suffix}"
            oss_policy_name = f"AmazonBedrockOSSPolicyForKnowledgeBase_{self.suffix}"
            vector_store_name = f"{kb_name}-{self.suffix}"
            index_name = f"{kb_name}-index-{self.suffix}"

            print("========================================================================================")
            print(f"Step 1 - Creating Knowledge Base Execution Role ({kb_execution_role_name}) and Policies")
            
            # Create execution role for Bedrock KB
            bedrock_kb_execution_role = self.create_bedrock_kb_execution_role(
                kb_execution_role_name,
                embedding_model,
                fm_policy_name,

                
            )
            print(f"Created Knowledge Base Execution Role: {bedrock_kb_execution_role}")
            print(bedrock_kb_execution_role)

            print("========================================================================================")
            print(f"Step 2 - Creating OSS encryption, network and data access policies")
            
            # Create OSS policies
            encryption_policy, network_policy, access_policy = self.create_policies_in_oss(
                encryption_policy_name,
                vector_store_name,
                network_policy_name,
                bedrock_kb_execution_role,
                access_policy_name,
            )

            print("========================================================================================")
            print(f"Step 3 - Creating OSS Collection (this step takes a couple of minutes to complete)")
            
            # Create OpenSearch Service
            host, collection, collection_id, collection_arn = self.create_oss(
                vector_store_name,
                oss_policy_name,
                bedrock_kb_execution_role,
                kb_execution_role_name

            )

            # Build the OpenSearch client
            self.oss_client = OpenSearch(
                hosts=[{"host": host, "port": 443}],
                http_auth=self.awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=300,
            )

            print("========================================================================================")
            print(f"Step 4 - Creating OSS Vector Index")
            self.create_vector_index(index_name)

            print("========================================================================================")
            print(f"Step 5 - Creating Knowledge Base with Confluence Data Source")
            
            # Create Knowledge Base with Confluence configuration
            knowledge_base, data_source = self.create_knowledge_base(
                kb_name,
                kb_description,
                confluence_url,
                index_name,
                secret_arn,
                embedding_model,
                collection_arn,
                bedrock_kb_execution_role,
                
            )

            # Wait for KB creation to complete
            interactive_sleep(60)
            
            print("========================================================================================")
            kb_id = knowledge_base["knowledgeBaseId"]
            ds_id = data_source["dataSourceId"]

        return kb_id, ds_id



    def create_s3_bucket(self, bucket_name: str):
        """
        Check if bucket exists, and if not create S3 bucket for knowledge base data source
        Args:
            bucket_name: s3 bucket name
        """
        self.data_bucket_name = bucket_name
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"Bucket {bucket_name} already exists - retrieving it!")
        except ClientError as e:
            print(f"Creating bucket {bucket_name}")
            if self.region_name == "us-east-1":
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": self.region_name},
                )

    def get_data_bucket_name(self):
        return self.data_bucket_name
    

    def create_bedrock_kb_execution_role(
        self,
        role_name: str,
        embedding_model: str,
        secret_arn: str
    ) -> str:
        """
        Creates IAM role and policies needed for a Knowledge Base with Confluence data source
        
        Args:
            role_name: Name of the IAM role to create
            embedding_model: Name of the embedding model to be used
            secret_arn: ARN of the secret containing Confluence credentials
            
        Returns:
            str: ARN of the created IAM role
        """
        try:
            # Create the trust policy for the role
            assume_role_policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "bedrock.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }

            # Create the role
            print(role_name)
            try:
                role = self.iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
                    Description="IAM role for Amazon Bedrock Knowledge Base with Confluence integration"
                )
                print(f"Created IAM role: {role_name}")
            except self.iam_client.exceptions.EntityAlreadyExistsException:
                role = self.iam_client.get_role(RoleName=role_name)
                print(f"Retrieved existing IAM role: {role_name}")

            role_arn = role['Role']['Arn']

            # Create policy for Foundation Model access
            fm_policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel"
                        ],
                        "Resource": [
                            f"arn:aws:bedrock:{self.region_name}::foundation-model/{embedding_model}"
                        ]
                    }
                ]
            }

            fm_policy_name = f"{role_name}-fm-policy"
            try:
                fm_policy = self.iam_client.create_policy(
                    PolicyName=fm_policy_name,
                    PolicyDocument=json.dumps(fm_policy_document),
                    Description="Policy for Bedrock Foundation Model access"
                )
                print(f"Created Foundation Model policy: {fm_policy_name}")
            except self.iam_client.exceptions.EntityAlreadyExistsException:
                fm_policy = self.iam_client.get_policy(
                    PolicyArn=f"arn:aws:iam::{self.account_number}:policy/{fm_policy_name}"
                )
                print(f"Retrieved existing Foundation Model policy: {fm_policy_name}")

            # Create policy for Secrets Manager access
            secrets_policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "secretsmanager:GetSecretValue"
                        ],
                        "Resource": [
                            "*"
                        ]
                    }
                ]
            }

            secrets_policy_name = f"{role_name}-secrets-policy"
            try:
                secrets_policy = self.iam_client.create_policy(
                    PolicyName=secrets_policy_name,
                    PolicyDocument=json.dumps(secrets_policy_document),
                    Description="Policy for Secrets Manager access"
                )
                print(f"Created Secrets Manager policy: {secrets_policy_name}")
            except self.iam_client.exceptions.EntityAlreadyExistsException:
                secrets_policy = self.iam_client.get_policy(
                    PolicyArn=f"arn:aws:iam::{self.account_number}:policy/{secrets_policy_name}"
                )
                print(f"Retrieved existing Secrets Manager policy: {secrets_policy_name}")

            # Create policy for OpenSearch Serverless access
            oss_policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "aoss:CreateCollection",
                            "aoss:DeleteCollection",
                            "aoss:BatchGetCollection",
                            "aoss:CreateSecurityPolicy",
                            "aoss:CreateAccessPolicy",
                            "aoss:GetAccessPolicy",
                            "aoss:CreateSecurityPolicy",
                            "aoss:GetSecurityPolicy",
                            "aoss:UpdateSecurityPolicy",
                            "aoss:CreateServerlessVpcEndpoint",
                            "aoss:DeleteServerlessVpcEndpoint",
                            "aoss:ListServerlessVpcEndpoints",
                            "aoss:ListCollections",
                            "aoss:APIAccessAll"
                        ],
                        "Resource": "*"
                    }
                ]
            }

            oss_policy_name = f"{role_name}-oss-policy"
            try:
                oss_policy = self.iam_client.create_policy(
                    PolicyName=oss_policy_name,
                    PolicyDocument=json.dumps(oss_policy_document),
                    Description="Policy for OpenSearch Serverless access"
                )
                print(f"Created OpenSearch Serverless policy: {oss_policy_name}")
            except self.iam_client.exceptions.EntityAlreadyExistsException:
                oss_policy = self.iam_client.get_policy(
                    PolicyArn=f"arn:aws:iam::{self.account_number}:policy/{oss_policy_name}"
                )
                print(f"Retrieved existing OpenSearch Serverless policy: {oss_policy_name}")

            # Attach policies to the role
            try:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=f"arn:aws:iam::{self.account_number}:policy/{fm_policy_name}"
                )
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=f"arn:aws:iam::{self.account_number}:policy/{secrets_policy_name}"
                )
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=f"arn:aws:iam::{self.account_number}:policy/{oss_policy_name}"
                )
                print("Successfully attached all policies to the role")
            except Exception as e:
                print(f"Error attaching policies to role: {str(e)}")
                raise
            '''
            # Add additional required AWS managed policies
            managed_policies = [
                "service-role/AWSBedrockKnowledgeBaseFoundationModelPolicy",
                "service-role/AWSBedrockKnowledgeBaseVectorSearchPolicy"
            ]

            for policy in managed_policies:
                try:
                    self.iam_client.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=f"arn:aws:iam::aws:policy/{policy}"
                    )
                    print(f"Attached managed policy: {policy}")
                except Exception as e:
                    print(f"Error attaching managed policy {policy}: {str(e)}")
                    raise
            '''

            # Wait for role to propagate
            time.sleep(10)
            
            return role_arn

        except Exception as e:
            print(f"Error creating IAM role and policies: {str(e)}")
            raise


    


    def create_oss_policy_attach_bedrock_execution_role(
        self, collection_id: str, oss_policy_name: str, bedrock_kb_execution_role: str, kb_execution_role_name: str
    ):
        """
        Create OpenSearch Serverless policy and attach it to the Knowledge Base Execution role.
        If policy already exists, attaches it
        Args:
            collection_id: collection id
            oss_policy_name: opensearch serverless policy name
            bedrock_kb_execution_role: knowledge base execution role

        Returns:
            created: bool - boolean to indicate if role was created
        """
        # define oss policy document
        oss_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["aoss:APIAccessAll"],
                    "Resource": [
                        f"arn:aws:aoss:{self.region_name}:{self.account_number}:collection/{collection_id}"
                    ],
                }
            ],
        }

        oss_policy_arn = f"arn:aws:iam::{self.account_number}:policy/{oss_policy_name}"
        created = False
        try:
            self.iam_client.create_policy(
                PolicyName=oss_policy_name,
                PolicyDocument=json.dumps(oss_policy_document),
                Description="Policy for accessing opensearch serverless",
            )
            created = True
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            print(f"Policy {oss_policy_arn} already exists, updating it")
        print("Opensearch serverless arn: ", oss_policy_arn)

        self.iam_client.attach_role_policy(
            RoleName=kb_execution_role_name,
            PolicyArn=oss_policy_arn,
        )
        return created

    def create_policies_in_oss(
        self,
        encryption_policy_name: str,
        vector_store_name: str,
        network_policy_name: str,
        bedrock_kb_execution_role: str,
        access_policy_name: str,
    ):
        """
        Create OpenSearch Serverless encryption, network and data access policies.
        If policies already exist, retrieve them
        Args:
            encryption_policy_name: name of the data encryption policy
            vector_store_name: name of the vector store
            network_policy_name: name of the network policy
            bedrock_kb_execution_role: name of the knowledge base execution role
            access_policy_name: name of the data access policy

        Returns:
            encryption_policy, network_policy, access_policy
        """
        try:
            encryption_policy = self.aoss_client.create_security_policy(
                name=encryption_policy_name,
                policy=json.dumps(
                    {
                        "Rules": [
                            {
                                "Resource": ["collection/" + vector_store_name],
                                "ResourceType": "collection",
                            }
                        ],
                        "AWSOwnedKey": True,
                    }
                ),
                type="encryption",
            )
        except self.aoss_client.exceptions.ConflictException:
            print(f"{encryption_policy_name} already exists, retrieving it!")
            encryption_policy = self.aoss_client.get_security_policy(
                name=encryption_policy_name, type="encryption"
            )

        try:
            network_policy = self.aoss_client.create_security_policy(
                name=network_policy_name,
                policy=json.dumps(
                    [
                        {
                            "Rules": [
                                {
                                    "Resource": ["collection/" + vector_store_name],
                                    "ResourceType": "collection",
                                }
                            ],
                            "AllowFromPublic": True,
                        }
                    ]
                ),
                type="network",
            )
        except self.aoss_client.exceptions.ConflictException:
            print(f"{network_policy_name} already exists, retrieving it!")
            network_policy = self.aoss_client.get_security_policy(
                name=network_policy_name, type="network"
            )

        try:
            access_policy = self.aoss_client.create_access_policy(
                name=access_policy_name,
                policy=json.dumps(
                    [
                        {
                            "Rules": [
                                {
                                    "Resource": ["collection/" + vector_store_name],
                                    "Permission": [
                                        "aoss:CreateCollectionItems",
                                        "aoss:DeleteCollectionItems",
                                        "aoss:UpdateCollectionItems",
                                        "aoss:DescribeCollectionItems",
                                    ],
                                    "ResourceType": "collection",
                                },
                                {
                                    "Resource": ["index/" + vector_store_name + "/*"],
                                    "Permission": [
                                        "aoss:CreateIndex",
                                        "aoss:DeleteIndex",
                                        "aoss:UpdateIndex",
                                        "aoss:DescribeIndex",
                                        "aoss:ReadDocument",
                                        "aoss:WriteDocument",
                                    ],
                                    "ResourceType": "index",
                                },
                            ],
                            "Principal": [
                                self.identity,
                                bedrock_kb_execution_role,
                            ],
                            "Description": "Easy data policy",
                        }
                    ]
                ),
                type="data",
            )
        except self.aoss_client.exceptions.ConflictException:
            print(f"{access_policy_name} already exists, retrieving it!")
            access_policy = self.aoss_client.get_access_policy(
                name=access_policy_name, type="data"
            )
        return encryption_policy, network_policy, access_policy

    def create_oss(
        self,
        vector_store_name: str,
        oss_policy_name: str,
        bedrock_kb_execution_role: str,
        kb_execution_role_name: str
    ):
        """
        Create OpenSearch Serverless Collection. If already existent, retrieve
        Args:
            vector_store_name: name of the vector store
            oss_policy_name: name of the opensearch serverless access policy
            bedrock_kb_execution_role: name of the knowledge base execution role
        """
        try:
            collection = self.aoss_client.create_collection(
                name=vector_store_name, type="VECTORSEARCH"
            )
            collection_id = collection["createCollectionDetail"]["id"]
            collection_arn = collection["createCollectionDetail"]["arn"]
        except self.aoss_client.exceptions.ConflictException:
            collection = self.aoss_client.batch_get_collection(
                names=[vector_store_name]
            )["collectionDetails"][0]
            pp.pprint(collection)
            collection_id = collection["id"]
            collection_arn = collection["arn"]
        pp.pprint(collection)

        # Get the OpenSearch serverless collection URL
        host = collection_id + "." + self.region_name + ".aoss.amazonaws.com"
        print(host)
        # wait for collection creation
        # This can take couple of minutes to finish
        response = self.aoss_client.batch_get_collection(names=[vector_store_name])
        # Periodically check collection status
        while (response["collectionDetails"][0]["status"]) == "CREATING":
            print("Creating collection...")
            interactive_sleep(30)
            response = self.aoss_client.batch_get_collection(names=[vector_store_name])
        print("\nCollection successfully created:")
        pp.pprint(response["collectionDetails"])
        # create opensearch serverless access policy and attach it to Bedrock execution role
        try:
            created = self.create_oss_policy_attach_bedrock_execution_role(
                collection_id, oss_policy_name, bedrock_kb_execution_role, kb_execution_role_name
            )
            if created:
                # It can take up to a minute for data access rules to be enforced
                print(
                    "Sleeping for a minute to ensure data access rules have been enforced"
                )
                interactive_sleep(60)
            return host, collection, collection_id, collection_arn
        except Exception as e:
            print("Policy already exists")
            pp.pprint(e)

    def create_vector_index(self, index_name: str):
        """
        Create OpenSearch Serverless vector index. If existent, ignore
        Args:
            index_name: name of the vector index
        """
        body_json = {
            "settings": {
                "index.knn": "true",
                "number_of_shards": 1,
                "knn.algo_param.ef_search": 512,
                "number_of_replicas": 0,
            },
            "mappings": {
                "properties": {
                    "vector": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {
                            "name": "hnsw",
                            "engine": "faiss",
                            "space_type": "l2",
                        },
                    },
                    "text": {"type": "text"},
                    "text-metadata": {"type": "text"},
                }
            },
        }

        # Create index
        try:
            response = self.oss_client.indices.create(
                index=index_name, body=json.dumps(body_json)
            )
            print("\nCreating index:")
            pp.pprint(response)

            # index creation can take up to a minute
            interactive_sleep(60)
        except RequestError as e:
            # you can delete the index if its already exists
            self.oss_client.indices.delete(index=index_name)
            print(
                f"Error while trying to create the index, with error {e.error}\nyou may unmark the delete above to "
                f"delete, and recreate the index"
            )

    @retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=7)
    def create_knowledge_base(
        self,
        kb_name: str,
        kb_description: str,
        confluence_url: str,
        index_name: str,
        secret_arn: str,
        embedding_model: str,
        collection_arn: str,
        bedrock_kb_execution_role: str,
    
    ):
        """
        Create Knowledge Base and its Data Source. If existent, retrieve
        Args:
            collection_arn: ARN of the opensearch serverless collection
            index_name: name of the opensearch serverless index
            bucket_name: name of the s3 bucket containing the knowledge base data
            embedding_model: id of the embedding model used
            kb_name: knowledge base name
            kb_description: knowledge base description
            bedrock_kb_execution_role: knowledge base execution role

        Returns:
            knowledge base object,
            data source object
        """
        opensearch_serverless_configuration = {
            "collectionArn": collection_arn,
            "vectorIndexName": index_name,
            "fieldMapping": {
                "vectorField": "vector",
                "textField": "text",
                "metadataField": "text-metadata",
            },
        }

        # Ingest strategy - How to ingest data from the data source
        chunking_strategy_configuration = {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 512,
                "overlapPercentage": 20,
            },
        }


        # The embedding model used by Bedrock to embed ingested documents, and realtime prompts
        embedding_model_arn = (
            f"arn:aws:bedrock:{self.region_name}::foundation-model/{embedding_model}"
        )
        print(
            str(
                {
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": embedding_model_arn
                    },
                }
            )
        )
        try:
            create_kb_response = self.bedrock_agent_client.create_knowledge_base(
                name=kb_name,
                description=kb_description,
                roleArn=bedrock_kb_execution_role,
                knowledgeBaseConfiguration={
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": embedding_model_arn
                    },
                },
                storageConfiguration={
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": opensearch_serverless_configuration,
                },
            )
            kb = create_kb_response["knowledgeBase"]
            pp.pprint(kb)
        except self.bedrock_agent_client.exceptions.ConflictException:
            kbs = self.bedrock_agent_client.list_knowledge_bases(maxResults=100)
            kb_id = None
            for kb in kbs["knowledgeBaseSummaries"]:
                if kb["name"] == kb_name:
                    kb_id = kb["knowledgeBaseId"]
            response = self.bedrock_agent_client.get_knowledge_base(
                knowledgeBaseId=kb_id
            )
            kb = response["knowledgeBase"]
            pp.pprint(kb)

        # Create a DataSource in KnowledgeBase
        try:
            create_ds_response = self.bedrock_agent_client.create_data_source(
                name=f"{kb_name}-confluence",
                description=f"Confluence data source for {kb_name}",
                knowledgeBaseId=kb["knowledgeBaseId"],
                dataSourceConfiguration={
        "type": "CONFLUENCE",
        "confluenceConfiguration": {
            "sourceConfiguration": {
                "hostUrl": confluence_url,
                "hostType": "SAAS",  # or "SERVER" depending on your Confluence setup
                "authType": "BASIC",
                "credentialsSecretArn": secret_arn
            },
        }
    },
                vectorIngestionConfiguration={
                    "chunkingConfiguration": {
                        "chunkingStrategy": "FIXED_SIZE",
                        "fixedSizeChunkingConfiguration": {
                            "maxTokens": 300,
                            "overlapPercentage": 20
                        }
                    }
                }
            )
            ds = create_ds_response["dataSource"]
            pp.pprint(ds)
        except self.bedrock_agent_client.exceptions.ConflictException:
            ds_id = self.bedrock_agent_client.list_data_sources(
                knowledgeBaseId=kb["knowledgeBaseId"], maxResults=100
            )["dataSourceSummaries"][0]["dataSourceId"]
            get_ds_response = self.bedrock_agent_client.get_data_source(
                dataSourceId=ds_id, knowledgeBaseId=kb["knowledgeBaseId"]
            )
            ds = get_ds_response["dataSource"]
            pp.pprint(ds)
        return kb, ds

    def synchronize_data(self, kb_id, ds_id):
        """
        Start an ingestion job to synchronize data from an S3 bucket to the Knowledge Base
        and waits for the job to be completed
        Args:
            kb_id: knowledge base id
            ds_id: data source id
        """
        # ensure that the kb is available
        i_status = ["CREATING", "DELETING", "UPDATING"]
        while (
            self.bedrock_agent_client.get_knowledge_base(knowledgeBaseId=kb_id)[
                "knowledgeBase"
            ]["status"]
            in i_status
        ):
            time.sleep(10)
        # Start an ingestion job
        start_job_response = self.bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=kb_id, dataSourceId=ds_id
        )
        job = start_job_response["ingestionJob"]
        pp.pprint(job)
        # Get job
        while job["status"] != "COMPLETE" and job["status"] != "FAILED":
            get_job_response = self.bedrock_agent_client.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job["ingestionJobId"],
            )
            job = get_job_response["ingestionJob"]
            interactive_sleep(5)
        pp.pprint(job)
        # interactive_sleep(40)

    def get_kb(self, kb_id):
        """
        Get KB details
        Args:
            kb_id: knowledge base id
        """
        get_job_response = self.bedrock_agent_client.get_knowledge_base(
            knowledgeBaseId=kb_id
        )
        return get_job_response

    def delete_kb(
        self,
        kb_name: str,
        delete_s3_bucket: bool = True,
        delete_iam_roles_and_policies: bool = True,
        delete_aoss: bool = True,
    ):
        """
        Delete the Knowledge Base resources
        Args:
            kb_name: name of the knowledge base to delete
            delete_s3_bucket (bool): boolean to indicate if s3 bucket should also be deleted
            delete_iam_roles_and_policies (bool): boolean to indicate if IAM roles and Policies should also be deleted
            delete_aoss: boolean to indicate if amazon opensearch serverless resources should also be deleted
        """
        kbs_available = self.bedrock_agent_client.list_knowledge_bases(
            maxResults=100,
        )
        kb_id = None
        ds_id = None
        for kb in kbs_available["knowledgeBaseSummaries"]:
            if kb_name == kb["name"]:
                kb_id = kb["knowledgeBaseId"]
        kb_details = self.bedrock_agent_client.get_knowledge_base(knowledgeBaseId=kb_id)
        kb_role = kb_details["knowledgeBase"]["roleArn"].split("/")[1]
        collection_id = kb_details["knowledgeBase"]["storageConfiguration"][
            "opensearchServerlessConfiguration"
        ]["collectionArn"].split("/")[1]
        index_name = kb_details["knowledgeBase"]["storageConfiguration"][
            "opensearchServerlessConfiguration"
        ]["vectorIndexName"]

        encryption_policies = self.aoss_client.list_security_policies(
            maxResults=100, type="encryption"
        )
        encryption_policy_name = None
        for ep in encryption_policies["securityPolicySummaries"]:
            if ep["name"].startswith(kb_name):
                encryption_policy_name = ep["name"]

        network_policies = self.aoss_client.list_security_policies(
            maxResults=100, type="network"
        )
        network_policy_name = None
        for np in network_policies["securityPolicySummaries"]:
            if np["name"].startswith(kb_name):
                network_policy_name = np["name"]

        data_policies = self.aoss_client.list_access_policies(
            maxResults=100, type="data"
        )
        access_policy_name = None
        for dp in data_policies["accessPolicySummaries"]:
            if dp["name"].startswith(kb_name):
                access_policy_name = dp["name"]

        ds_available = self.bedrock_agent_client.list_data_sources(
            knowledgeBaseId=kb_id,
            maxResults=100,
        )
        for ds in ds_available["dataSourceSummaries"]:
            if kb_id == ds["knowledgeBaseId"]:
                ds_id = ds["dataSourceId"]
        ds_details = self.bedrock_agent_client.get_data_source(
            dataSourceId=ds_id,
            knowledgeBaseId=kb_id,
        )
        bucket_name = ds_details["dataSource"]["dataSourceConfiguration"][
            "s3Configuration"
        ]["bucketArn"].replace("arn:aws:s3:::", "")
        try:
            self.bedrock_agent_client.delete_data_source(
                dataSourceId=ds_id, knowledgeBaseId=kb_id
            )
            print("Data Source deleted successfully!")
        except Exception as e:
            print(e)
        try:
            self.bedrock_agent_client.delete_knowledge_base(knowledgeBaseId=kb_id)
            print("Knowledge Base deleted successfully!")
        except Exception as e:
            print(e)
        if delete_aoss:
            try:
                self.oss_client.indices.delete(index=index_name)
                print("OpenSource Serveless Index deleted successfully!")
            except Exception as e:
                print(e)
            try:
                self.aoss_client.delete_collection(id=collection_id)
                print("OpenSource Collection Index deleted successfully!")
            except Exception as e:
                print(e)
            try:
                self.aoss_client.delete_access_policy(
                    type="data", name=access_policy_name
                )
                print("OpenSource Serveless access policy deleted successfully!")
            except Exception as e:
                print(e)
            try:
                self.aoss_client.delete_security_policy(
                    type="network", name=network_policy_name
                )
                print("OpenSource Serveless network policy deleted successfully!")
            except Exception as e:
                print(e)
            try:
                self.aoss_client.delete_security_policy(
                    type="encryption", name=encryption_policy_name
                )
                print("OpenSource Serveless encryption policy deleted successfully!")
            except Exception as e:
                print(e)
        if delete_s3_bucket:
            try:
                self.delete_s3(bucket_name)
                print("Knowledge Base S3 bucket deleted successfully!")
            except Exception as e:
                print(e)
        if delete_iam_roles_and_policies:
            try:
                self.delete_iam_roles_and_policies(kb_role)
                print("Knowledge Base Roles and Policies deleted successfully!")
            except Exception as e:
                print(e)
        print("Resources deleted successfully!")

    def delete_iam_roles_and_policies(self, kb_execution_role_name: str):
        """
        Delete IAM Roles and policies used by the Knowledge Base
        Args:
            kb_execution_role_name: knowledge base execution role
        """
        attached_policies = self.iam_client.list_attached_role_policies(
            RoleName=kb_execution_role_name, MaxItems=100
        )
        policies_arns = []
        for policy in attached_policies["AttachedPolicies"]:
            policies_arns.append(policy["PolicyArn"])
        for policy in policies_arns:
            self.iam_client.detach_role_policy(
                RoleName=kb_execution_role_name, PolicyArn=policy
            )
            self.iam_client.delete_policy(PolicyArn=policy)
        self.iam_client.delete_role(RoleName=kb_execution_role_name)
        return 0

    def delete_s3(self, bucket_name: str):
        """
        Delete the objects contained in the Knowledge Base S3 bucket.
        Once the bucket is empty, delete the bucket
        Args:
            bucket_name: bucket name

        """
        objects = self.s3_client.list_objects(Bucket=bucket_name)
        if "Contents" in objects:
            for obj in objects["Contents"]:
                self.s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
        self.s3_client.delete_bucket(Bucket=bucket_name)

    def create_confluence_credentials_secret(
        self,
        secret_name: "Bedrock-Confluence-Secret",
        auth_type: str = "BASIC",
        username: str = None,
        password: str = None,
        region_name: str = self.region_name
    ) -> dict:
        """
        Creates or updates a secret in AWS Secrets Manager for Confluence credentials.
        Supports Basic Authentication, OAuth 2.0, and Personal Access Token (PAT).

        Args:
            secret_name: Name of the secret to create
            auth_type: Authentication type ('BASIC', 'OAUTH2', or 'PAT')
            username: Confluence username (for Basic auth)
            password: Confluence Token (for Basic auth)
            region_name: AWS region name (optional)

        Returns:
            dict: Response from Secrets Manager containing secret details
        """
        try:
            # Use provided region or default to instance region
            if region_name is None:
                region_name = self.region_name

            # Create Secrets Manager client
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=region_name
            )

            # Prepare secret value based on authentication type
            if auth_type.upper() == "BASIC":
                print("username is ")
                print(username)
                print("password is ")
                print(password)
                if not username or not password:
                    raise ValueError("Username and API token are required for Basic authentication")
                
                secret_value = {
                    "username": username,
                    "password": password
                }
                

            try:
                # Try to create new secret
                response = client.create_secret(
                    Name=secret_name,
                    Description=f'Confluence credentials for {auth_type} authentication',
                    SecretString=json.dumps(secret_value)
                )
                print(f"Created new secret: {secret_name}")

            except client.exceptions.ResourceExistsException:
                # If secret exists, update it
                response = client.update_secret(
                    SecretId=secret_name,
                    SecretString=json.dumps(secret_value)
                )
                print(f"Updated existing secret: {secret_name}")

            # Add tags to the secret
            try:
                client.tag_resource(
                    SecretId=secret_name,
                    Tags=[
                        {
                            'Key': 'Service',
                            'Value': 'Confluence'
                        },
                        {
                            'Key': 'AuthType',
                            'Value': auth_type.upper()
                        }
                    ]
                )
            except Exception as e:
                print(f"Warning: Could not add tags to secret: {str(e)}")

            return response

        except Exception as e:
            print(f"Error managing Confluence credentials secret: {str(e)}")
            raise
