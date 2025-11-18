
PROBLEM STATEMENT AND JUSTIFICATION

Problem Statement

In large-scale enterprise systems with numerous microservices, the time taken to determine the root cause of a production issue is significantly high. This delay (high Mean Time to Resolution, or MTTR) is caused by:

Data Overload: Massive volumes of logs and alerts from dozens or hundreds of services.

Information Silos: Critical knowledge is scattered across different sources (logs, code, functional documentation, wikis, past incident tickets).
Contextual Complexity: A single issue can cascade, creating symptoms in multiple services far from the original fault.
The core problem is the lack of an intelligent, unified system that can automatically detect an issue, correlate it across all data silos, and provide a human-understandable diagnosis in minutes, not hours or days

Justification of Problem Selection
The selection of this problem is justified by its direct and significant business impact.

Economic Impact: System downtime is expensive. Every minute a production system is down or degraded translates to lost revenue, reduced productivity, and potential damage to the company’s reputation.
Operational Inefficiency: Manual RCA consumes a disproportionate amount of senior engi- neering and SRE (Site Reliability Engineering) time. This is a highly inefficient use of skilled resources who could be focusing on developing new features or improving system architecture.
Scalability Challenge: As systems grow in complexity, the combinatorial explosion of potential failure points makes manual RCA increasingly infeasible. A scalable, automated solution is not just a nice-to-have but a future necessity for growth.
By automating RCA, we can directly reduce MTTR, free up valuable engineering resources, and
create more resilient, reliable, and scalable enterprise systems.



LITERATURE SURVEY AND POSSIBLE APPROACHES

Literature Survey
The field of automated RCA and AIOps has evolved through several paradigms.

Rule-Based Systems: Early approaches (e.g., Nagios, Zabbix) rely on predefined rules and thresholds. They are effective for known failure modes but are brittle, require constant manual updating, and cannot detect novel or unknown unknown issues.
Statistical and Classical ML Approaches: This wave introduced anomaly detection on log and metric data. Methods like ARIMA, Isolation Forest, and One-Class SVMs can identify deviations from normal behavior. However, they often generate many false positives and lack explanatory power; they can tell that something is wrong, but not why.
Deep Learning for Anomaly Detection: More recent work uses deep learning (e.g., LSTMs, Autoencoders) for log analysis. Models like DeepLog learn normal log patterns and flag deviations. While more powerful, they are often treated as black boxes and still primarily focus only on log data, ignoring other contexts.
AIOps Platforms: Commercial platforms (e.g., Dynatrace, Datadog) integrate anomaly detec- tion with event correlation. They are powerful but can be proprietary, expensive, and may still struggle to synthesize unstructured data from documentation or code.
Generative AI (RAG): The most recent approach, and the one this project builds on, is the use of Large Language Models (LLMs) with Retrieval-Augmented Generation (RAG). This allows the model to ground its reasoning in factual, domain-specific data, which is a perfect fit for RCA.



Possible Approaches
Our proposed solution is a multi-stage pipeline that addresses the user’s challenge points directly.

Component 1: Anomaly Detection
This is the trigger for our agent. The challenge is to be accurate without being overly complex for a
baseline.

Option 1: Classical ML. This algorithm is efficient, unsu- pervised, and effective for finding unusual data points. It can be trained on vectors derived from log lines (e.g., TF-IDF or log template embeddings) to find anomalous logs.
Option 2 : Deep Learning - This approach would learn the normal sequence of logs. When a new sequence of logs doesn’t match what the model expects (high reconstruction error), it’s flagged as an anomaly. This is more powerful but requires more data and training.
Selected Initial Approach: We will start with an Isolation Forest model. It is faster to implement and provides a robust baseline. The system’s value is in the agentic reasoning that follows the anomaly, not just the anomaly detection itself.

Component 2: Knowledge Base and Retrieval	(RAG)
This addresses the pulling relevant docs challenge. The knowledge base will be a vector database
(e.g., ChromaDB, Elasticsearch).

Data Ingestion: All data sources (code, functional docs, wikis) will be chunked into meaningful segments.
Embedding: Each chunk will be converted into a vector embedding using a model like (Ex: all- MiniLM-L6-v2) or a domain-specific model.
Retrieval Strategy (Hybrid Search): This is key. We will not rely on semantic search alone. We will implement hybrid search, which combines:
Semantic Search (Vector): Finds documents that are conceptually similar to the anomaly log (e.g., database connection failure retrieves docs about DB timeout settings).

Keyword Search (e.g., BM25): Finds documents that contain exact terms, like a specific error code (ORA-01034) or service name (auth-service-v2).
This hybrid approach ensures we get both conceptually relevant and precisely matching information, which is critical for pulling the correct docs.

Component 3: Agentic Reasoning (GenAI)
Once an anomaly is detected and relevant documents are retrieved, they are passed to an AI agent.

Agent Framework: We will use a framework like LangChain or LlamaIndex to build the agent.

LLM Core: We will use a powerful LLM (e.g., via an API like GPT-4 or an open-source model like Llama 3) as the brain of the agent.
Prompt Engineering: The agent will be given a system prompt, the anomalous log, and the retrieved context (code snippets, doc sections). It will be instructed to act as an Expert SRE and provide a step-by-step analysis, a root cause hypothesis, and a recommended action.
