# Model Evaluation Pipeline

This diagram illustrates the 6-stage evaluation process for geotemporal reasoning.

```mermaid
graph TD
    %% Define the Flow
    Start([Start Evaluation]) --> Step1[Ground Truth Generation]
    Step1 --> Step2[Model Inference]
    Step2 --> Step3[Response Normalization]
    Step3 --> Step4{Exact Match Check}
    Step4 --> Step5[Error Analysis]
    Step5 --> Step6[Final Scoring]
    Step6 --> End([End Evaluation])

    %% Styling for GitHub
    classDef start_end fill:#f5f5f5,stroke:#333,stroke-width:2px;
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:1px;
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:1px;
    
    class Start,End start_end;
    class Step1,Step2,Step3,Step5,Step6 process;
    class Step4 decision;
