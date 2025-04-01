# Observability

## Setup

1. Follow setup instructions [here](../../../README.md#getting-started)
2. Create .env file using [.env.example](./.env.example) as reference
3. Make sure to PRODUCE_BEDROCK_OTEL_TRACES as `True`.
4. Run `python main.py`.
5. You can set `@observe(show_traces=True | False, save_traces=True | False)`.

- Setting `save_traces` to True saves the agent trace in `trace` directory.
- Setting `show_traces` to True prints the agent trace in `console`.

<details>
<summary>
<h2>Langfuse<h2>
</summary>
<p align="center">
    <a href="url"><img src="./images/langfuse.png" ></a>
</p>
</details>

<details>
<summary>
<h2>Phoenix<h2>
</summary>
<p align="center">
    <a href="url"><img src="./images/phoenix.png" ></a>
</p>
</details>