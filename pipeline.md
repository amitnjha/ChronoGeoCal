## Evaluation Pipeline

To clearly illustrate the benchmarking methodology, we include a process figure that summarizes the full evaluation pipeline. The figure highlights how each stage contributes to a comprehensive, fair, and insightful assessment of model performance on geotemporal reasoning tasks.

```mermaid
flowchart TD
    A([Start Evaluation]) --> B[Deterministic Ground Truth Generation]
    B --> C[Model Inference]
    C --> D[Response Normalization and Cleaning]
    D --> E{Exact-Match Verification}

    E --> C1[Correct Response]
    E --> I1[Incorrect Response]

    C1 --> F[Final Scoring]
    I1 --> G[Error Analysis and Categorization]
    G --> F

    F --> H([End Evaluation])

    classDef startend fill:#f7f7f7,stroke:#333,stroke-width:2px,color:#111;
    classDef process fill:#e8f1ff,stroke:#2b6cb0,stroke-width:1.5px,color:#111;
    classDef decision fill:#fff6cc,stroke:#d69e2e,stroke-width:1.5px,color:#111;
    classDef analysis fill:#f3e8ff,stroke:#805ad5,stroke-width:1.5px,color:#111;
    classDef tag fill:#f2f2f2,stroke:#888,stroke-width:1.2px,color:#111;

    class A,H startend;
    class B,C,D,F process;
    class E decision;
    class G analysis;
    class C1,I1 tag;
```

This benchmarking pipeline begins with deterministic ground-truth generation using formal calendar and time zone rules. Each prompt is then evaluated through standardized model inference, followed by response normalization to remove formatting artifacts. Exact-match verification ensures strict and reproducible scoring, while error analysis provides additional insight into common failure modes. Together, these stages deliver a comprehensive evaluation framework that is fair across models and informative for understanding both strengths and weaknesses.
