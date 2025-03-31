from crewai_tools import RagTool

pdf_search_tool = RagTool(
    config=dict(
        llm=dict(
            provider="aws_bedrock",
            config=dict(
                model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            ),
        ),
        embedder=dict(
            provider="aws_bedrock",
            config=dict(
                model="amazon.titan-embed-text-v2:0",
            ),
        ),
    ),
)


pdf_search_tool.add(
    "https://www.aboutamazon.com/news/company-news/amazon-ceo-andy-jassy-2023-letter-to-shareholders"
)
