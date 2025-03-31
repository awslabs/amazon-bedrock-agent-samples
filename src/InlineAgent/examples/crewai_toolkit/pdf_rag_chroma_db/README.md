# PDF Rag with Chroma database Agent

<p align="center">
  <a href="https://docs.crewai.com/tools/pdfsearchtool"><img src="https://img.shields.io/badge/CrewAI-PDFSearchTool-blue" /></a>
</p>

1. Follow setup instructions [here](../../../README.md#getting-started)
2. Create .env file with [.env.example](./.env.example)

![env](./images/env.png)

3. Install requirements

```bash
pip install -r requirements
```

4. Ingest pdf in Chroma database

```python
python ingest.py
```

5. Run example `python main.py`
