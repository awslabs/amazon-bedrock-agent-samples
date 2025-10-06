# Startup Advisor Agent

Have a new startup in mind, but haven't quite hired your marketing staff? Use this Startup Advisrt agent to do your market research, come up with campaign ideas, and write effective campaign copy. It uses a set of 5 sub-agents to get the job done these include Lead Market Analyst, Content Creator, Chief Conent Creator, Chief Stategist, and Agent Storage Manager.

![architecture](/images/architecture.gif)

## Prerequisites

1. Clone and install repository on your host computer

Linux
```bash
git clone https://github.com/awslabs/amazon-bedrock-agent-samples

cd amazon-bedrock-agent-samples

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r src/requirements.txt
```
Windows
```bash
git clone https://github.com/awslabs/amazon-bedrock-agent-samples

cd amazon-bedrock-agent-samples

python -m venv .venv

.\.venv\Scripts\activate

python -m pip install --upgrade pip

pip install -r src\requirements.txt
```

2. Deploy Web Search tool

Follow instructions [here](/src/shared/web_search/).

3. Deploy Working Memory tool

Follow instructions [here](/src/shared/working_memory/).

## Usage & Sample Prompts


1. Deploy Amazon Bedrock Agents

```bash
python3 examples/multi_agent_collaboration/startup_advisor_agent/main.py \
--recreate_agents "true"
```

2. Invoke

```bash
python3 examples/multi_agent_collaboration/startup_advisor_agent/main.py \
--recreate_agents "false" \
--web_domain "flyingCars.com" \
--project "FlyingCars wants to be the leading supplier of flying cars. The project is to build an innovative marketing strategy to showcase FlyingCars' advancedofferings, emphasizing ease of use, cost effectiveness, productivity, and safety. Target high net worth individuals, highlighting success stories and transformative 
potential. Be sure to include a draft for a video ad."
```

3. Cleanup

```bash
python3 examples/multi_agent_collaboration/startup_advisor_agent/main.py \
--clean_up "true"
```

## License

This project is licensed under the Apache-2.0 License.
