# Investment Research Assistant Agent

Investment Research supervisor agent has three collaborators, a News agent, a Quantitative Analysis Data agent, and a Smart Summarizer agent. These specialists are orchestrated to perform investment analysis for a given stock ticker based on the latest news and recent stock price movements. 

## Architecture Diagram

![architecture](./architecture.jpg)


## Prerequisites

1. Open a terminal then clone and install repository, setup environment

```bash
git clone https://github.com/awslabs/amazon-bedrock-agent-samples

cd amazon-bedrock-agent-samples

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r src/requirements.txt
```

2. Deploy Web Search tool

Follow instructions [here](/src/shared/web_search/).

3. Deploy Stock Data Lookup and Portfolio Optimization tool

Follow instructions [here](/src/shared/stock_data/).


### For main.ipynb

Run through the cells in the notebook, attach appropriate permissions as needed. 

## License

This project is licensed under the Apache-2.0 License.
