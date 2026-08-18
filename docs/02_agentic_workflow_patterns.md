# Chapter 2: Agentic Workflow Patterns

## Learning Objectives

By the end of this chapter, participants will be able to:

- Understand common agentic workflow patterns.
- Identify when each pattern should be used.
- Compare the strengths and limitations of different workflows.
- Map workflow patterns to real-world AI applications.
- Understand how these patterns translate into LangGraph graphs.

---

## Introduction

Real-world AI applications rarely consist of a single LLM call. Instead, they are composed of multiple reasoning steps, decision points, tool invocations, and interactions with external systems.

Over time, several workflow patterns have emerged as effective ways to organize these interactions.

These patterns provide reusable solutions for common problems such as routing requests, coordinating multiple tasks, evaluating outputs, and managing complex reasoning processes.

Understanding these patterns is essential before learning LangGraph because each pattern can be naturally represented as a graph of interconnected nodes.

---

## Common Agentic Workflow Patterns

| Pattern | Purpose | Example Use Case |
|----------|---------|------------------|
| Chain | Sequential execution | Summarization pipeline |
| Router | Dynamic path selection | Customer support routing |
| Parallelization | Execute independent tasks simultaneously | Multi-document analysis |
| Evaluator–Optimizer | Improve output iteratively | Code generation and refinement |
| Orchestrator–Worker | Divide work among specialized workers | Report generation |
| Reflection | Self-review and improvement | Essay writing |
| ReAct | Reason and act using tools | Research assistant |
| Plan-and-Execute | Plan first, execute later | Trip planning |

---

# 1. Chain Workflow

## Concept

A Chain workflow executes tasks in a fixed sequential order.

Each step receives the output of the previous step as its input.

```
Input
  │
  ▼
Step 1
  │
  ▼
Step 2
  │
  ▼
Step 3
  │
  ▼
Output
```

This is the simplest workflow pattern and is suitable when every request follows exactly the same sequence of operations.

### Advantages

- Easy to implement
- Predictable execution
- Simple debugging

### Limitations

- No branching
- No dynamic decision making
- Cannot adapt to changing conditions

### Example Applications

- Text summarization
- Translation pipeline
- Data cleaning
- Report generation

---

# 2. Router Workflow

## Concept

A Router workflow dynamically selects the next execution path based on the characteristics of the input.

Unlike a Chain workflow, where every request follows the same sequence, a Router determines which branch should handle the current request.

```
              Input
                │
                ▼
             Router
        ┌───────┼────────┐
        ▼       ▼        ▼
   Path A   Path B   Path C
        │       │        │
        └───────┼────────┘
                ▼
             Final Output
```

The routing decision may be based on:

- User intent
- Input language
- Task type
- Sentiment
- Document category
- Confidence score
- Classification model output

### Advantages

- Dynamic execution
- Better scalability
- Specialized processing for different requests
- Reduced unnecessary computation

### Limitations

- Requires accurate routing logic
- Incorrect routing can reduce performance
- More complex than a simple chain

### Example Applications

- Customer support ticket routing
- Medical symptom classification
- Email categorization
- Intent detection for chatbots
- Document classification

### When Should You Use a Router?

Use a Router workflow when different inputs require different processing paths.

For example:

- Technical questions → Technical support agent
- Billing questions → Finance agent
- Sales inquiries → Sales agent

Instead of forcing every request through the same pipeline, the router directs each request to the most appropriate workflow.

### Chain vs Router

| Chain | Router |
|--------|--------|
| Fixed execution | Dynamic execution |
| Same path every time | Different paths depending on input |
| Simple implementation | More flexible |
| Suitable for predictable tasks | Suitable for heterogeneous tasks |

The Router pattern introduces the idea of **conditional execution**, which later becomes **conditional edges** in LangGraph.

---

# 3. Parallelization Workflow

## Concept

In a Parallelization workflow, multiple independent tasks are executed simultaneously. Since these tasks do not depend on one another, they can run concurrently, reducing the overall execution time.

```
             Input
               │
               ▼
      ┌────────┼────────┐
      ▼        ▼        ▼
   Task A   Task B   Task C
      │        │        │
      └────────┼────────┘
               ▼
        Combine Results
               │
               ▼
           Final Output
```

Unlike a Chain workflow, where each step waits for the previous one to complete, Parallelization allows multiple operations to proceed at the same time.

This pattern is particularly useful when each task performs a different analysis on the same input.

### Advantages

- Reduced execution time
- Better utilization of computational resources
- Independent tasks can scale separately
- Suitable for large-scale AI applications

### Limitations

- Tasks must be independent
- Synchronization is required before combining results
- Parallel execution may increase resource usage

### Example Applications

- Multi-document summarization
- Image captioning with multiple models
- Sentiment, topic, and keyword extraction in parallel
- Simultaneous API calls
- Multi-agent research systems

### When Should You Use Parallelization?

Use Parallelization when multiple analyses or operations can be performed independently.

For example, when analyzing a customer review, an AI system may simultaneously:

- Detect sentiment
- Extract key topics
- Identify named entities
- Generate a concise summary

Since each task works on the same input without depending on the others, they can execute concurrently and their outputs can later be combined into a single response.

### Chain vs Parallelization

| Chain | Parallelization |
|--------|-----------------|
| Sequential execution | Concurrent execution |
| Tasks depend on previous outputs | Tasks are independent |
| Simpler coordination | Requires result synchronization |
| Higher latency for long workflows | Lower latency when tasks can run together |

Parallelization is a common optimization technique in production AI systems, especially when multiple independent analyses are required.

### Real-World Example

Consider an AI assistant that receives the following request:

> "Analyze this product review."

Instead of performing one analysis after another, the system can execute several tasks simultaneously:

- Sentiment Analysis
- Emotion Detection
- Keyword Extraction
- Spam Detection
- Language Identification

Once all analyses are complete, their results are combined into a comprehensive report for the user.

This approach improves responsiveness while maintaining modularity.

---

# 4. Evaluator–Optimizer Workflow

## Concept

The Evaluator–Optimizer workflow separates the process of generating an output from evaluating its quality.

Instead of accepting the first response produced by an LLM, the system reviews the output, identifies weaknesses, and either approves it or requests another iteration.

```
            Input
              │
              ▼
         Generator
              │
              ▼
         Candidate Output
              │
              ▼
          Evaluator
         ┌────┴────┐
         │         │
    Approved     Needs Improvement
         │               │
         ▼               │
   Final Output ◄────────┘
```

The evaluation may be performed by:

- Another LLM
- A rule-based system
- A scoring model
- Human feedback
- Automated tests

The optimization cycle continues until predefined quality criteria are satisfied.

### Advantages

- Improves response quality
- Reduces hallucinations
- Enables iterative refinement
- Encourages more reliable outputs
- Separates generation from evaluation

### Limitations

- Higher latency due to multiple iterations
- Increased computational cost
- Requires a well-designed evaluation strategy
- Risk of endless refinement if stopping criteria are unclear

### Example Applications

- Code generation and review
- Essay writing
- Research report refinement
- SQL query validation
- Document proofreading
- AI-generated test case verification

### Real-World Example

Imagine an AI system that generates Python code for a user's request.

Instead of immediately returning the generated code, the workflow proceeds as follows:

1. Generate an initial solution.
2. Review the code for syntax errors and logical issues.
3. Suggest improvements or corrections.
4. Regenerate the code if necessary.
5. Return the improved version only after it satisfies the evaluation criteria.

This iterative refinement process often produces more reliable and maintainable code than a single-pass generation approach.

### Key Insight

The Evaluator–Optimizer pattern introduces a **feedback loop**, where outputs are assessed before they are accepted.

Unlike Chain or Router workflows, this pattern may revisit earlier steps multiple times, making it well suited for tasks where quality is more important than speed.

This concept is naturally represented in LangGraph using cycles, allowing nodes to loop back for additional refinement until a stopping condition is met.

---

# 5. Orchestrator–Worker Workflow

## Concept

The Orchestrator–Worker workflow divides a complex task into smaller, manageable subtasks. A central **Orchestrator** analyzes the overall objective, assigns specialized tasks to one or more **Worker** components, and combines their outputs into the final result.

```
                 User Request
                      │
                      ▼
                Orchestrator
          ┌────────┼────────┐
          ▼        ▼        ▼
      Worker A  Worker B  Worker C
          │        │        │
          └────────┼────────┘
                   ▼
            Aggregate Results
                   │
                   ▼
              Final Response
```

Unlike Parallelization, where tasks are simply executed simultaneously, the Orchestrator is responsible for deciding:

- What subtasks should be created
- Which worker should perform each task
- How the individual outputs should be combined

This makes the workflow suitable for solving complex problems that require task decomposition.

### Advantages

- Handles complex tasks efficiently
- Encourages modular system design
- Enables specialization among workers
- Easy to extend by adding new workers
- Supports scalable AI architectures

### Limitations

- More complex orchestration logic
- Communication overhead between workers
- Requires effective task decomposition
- Final quality depends on both orchestration and worker performance

### Example Applications

- Research assistants
- Report generation
- Software development assistants
- Financial analysis
- Medical decision support
- Multi-step business workflows

### Real-World Example

Suppose a user asks:

> "Prepare a market analysis report for the electric vehicle industry."

Instead of asking one model to perform the entire task, the Orchestrator can divide the work:

- **Worker A:** Collect industry trends
- **Worker B:** Analyze competitors
- **Worker C:** Summarize financial performance
- **Worker D:** Identify future opportunities

The Orchestrator then combines these outputs into a structured market analysis report.

This division of responsibilities improves both scalability and maintainability.

### Key Insight

The Orchestrator–Worker pattern demonstrates that intelligent systems do not always rely on a single AI model.

Instead, a central coordinator manages multiple specialized workers, each responsible for a specific aspect of the overall problem.

This architectural pattern forms the conceptual foundation for multi-agent systems and is commonly implemented in LangGraph using multiple interconnected nodes with clearly defined responsibilities.

---

# 6. Reflection Workflow

## Concept

The Reflection workflow enables an AI system to examine its own output, identify weaknesses, and improve its response before presenting it to the user.

Unlike the Evaluator–Optimizer workflow, where a separate evaluator reviews the generated output, Reflection focuses on **self-assessment**. The same reasoning system analyzes its own work and decides whether revisions are necessary.

```
            Input
              │
              ▼
        Initial Response
              │
              ▼
        Self Reflection
              │
      ┌───────┴────────┐
      │                │
      ▼                ▼
Looks Good      Needs Revision
      │                │
      ▼                │
 Final Output ◄────────┘
```

Reflection allows AI systems to reason about the quality, completeness, and correctness of their own responses before producing a final answer.

### Advantages

- Produces higher-quality responses
- Encourages deeper reasoning
- Helps detect inconsistencies
- Reduces incomplete answers
- Improves factual accuracy when combined with external verification

### Limitations

- Additional computation time
- Increased token usage
- Self-reflection may still overlook mistakes
- Requires clear stopping conditions to avoid unnecessary iterations

### Example Applications

- Essay writing
- Research reports
- Code explanation
- Technical documentation
- Legal document drafting
- Scientific writing

### Real-World Example

Suppose an AI assistant is asked to explain a machine learning concept.

The workflow might proceed as follows:

1. Generate an initial explanation.
2. Review the explanation for missing details.
3. Check whether important concepts have been omitted.
4. Simplify overly technical language where appropriate.
5. Produce a revised and more comprehensive explanation.

This process often results in responses that are clearer and more useful than a single-pass generation.

### Key Insight

Reflection introduces the idea that reasoning is an iterative process rather than a single event.

Instead of immediately accepting its first answer, an AI system pauses to examine its own reasoning, identify potential weaknesses, and improve the response.

In LangGraph, Reflection is naturally modeled using cycles that revisit reasoning nodes until a satisfactory result is achieved.

---

# 7. ReAct (Reason + Act)

## Concept

ReAct (Reason + Act) is a workflow pattern in which an AI system alternates between **reasoning** about a problem and **taking actions** using external tools.

Instead of producing an answer immediately, the agent repeatedly:

1. Thinks about the current situation.
2. Decides whether additional information or actions are required.
3. Uses an appropriate tool.
4. Observes the result.
5. Continues reasoning until the task is complete.

```
        User Request
              │
              ▼
          Reasoning
              │
              ▼
      Need a Tool?
       ┌────┴────┐
       │         │
      No        Yes
       │         │
       ▼         ▼
 Final Answer  Tool Call
                 │
                 ▼
            Observation
                 │
                 ▼
             Reasoning
```

The cycle continues until the agent determines that it has enough information to generate a reliable response.

### Advantages

- Enables dynamic decision-making
- Integrates external tools seamlessly
- Produces more reliable answers
- Reduces hallucinations by retrieving real-world information
- Well suited for open-ended tasks

### Limitations

- Higher execution time
- Increased token usage
- Depends on tool reliability
- Requires careful tool selection and permissions

### Example Applications

- Research assistants
- Customer support agents
- Coding assistants
- Travel planning
- Financial analysis
- Knowledge retrieval systems
- Personal productivity assistants

### Real-World Example

Suppose a user asks:

> "What is the current weather in Bengaluru, and should I carry an umbrella tomorrow?"

A ReAct-based agent might follow these steps:

1. Recognize that the answer requires current weather data.
2. Call a weather API.
3. Receive the latest forecast.
4. Analyze the forecast.
5. Generate a recommendation based on expected rainfall.

Instead of relying solely on its internal knowledge, the agent reasons about the task, retrieves external information, and incorporates that information into its final response.

### Key Insight

ReAct combines reasoning with action.

Rather than treating the language model as a standalone generator, it becomes a decision-making component that can determine when additional information is needed and how to obtain it.

This workflow forms the conceptual basis for many production AI agents and is one of the most common patterns implemented using LangGraph.

---

# 8. Plan-and-Execute Workflow

## Concept

The Plan-and-Execute workflow separates problem solving into two distinct phases:

1. **Planning** – The agent creates a strategy by decomposing the objective into smaller tasks.
2. **Execution** – The planned tasks are carried out one by one until the objective is completed.

Unlike ReAct, which alternates between reasoning and action at every step, Plan-and-Execute performs high-level planning first and then follows that plan during execution.

```
            User Request
                  │
                  ▼
             Planning Phase
                  │
                  ▼
        Task 1 → Task 2 → Task 3
                  │
                  ▼
            Execution Phase
                  │
                  ▼
             Final Response
```

This workflow is particularly effective for objectives that involve many dependent steps or long-running processes.

### Advantages

- Encourages structured problem solving
- Reduces unnecessary tool calls
- Easier to monitor long-running workflows
- Suitable for complex projects
- Improves transparency of execution

### Limitations

- Initial plan may be incomplete or incorrect
- Replanning may be required if conditions change
- Planning adds extra computation before execution

### Example Applications

- Travel planning
- Software development projects
- Research assistants
- Data analysis pipelines
- Project management
- Business process automation

### Real-World Example

Suppose a user asks:

> "Create a market entry strategy for launching an electric vehicle in India."

A Plan-and-Execute agent might proceed as follows:

1. Define the scope of the analysis.
2. Gather market data.
3. Analyze competitors.
4. Study government policies.
5. Estimate pricing.
6. Develop a launch strategy.
7. Produce the final report.

By creating a structured plan before execution, the workflow remains organized and easier to monitor.

### Key Insight

Plan-and-Execute separates strategic thinking from operational execution.

This distinction makes it well suited for large objectives where planning the overall approach before taking action leads to more organized and reliable workflows.

In LangGraph, planning and execution can be represented as separate subgraphs, allowing each phase to evolve independently.

---

# Workflow Pattern Comparison

| Pattern | Dynamic | Uses Tools | Looping | Best For |
|----------|:-------:|:----------:|:-------:|----------|
| Chain | ❌ | Optional | ❌ | Fixed sequential tasks |
| Router | ✅ | Optional | ❌ | Intent-based routing |
| Parallelization | Partial | Optional | ❌ | Independent concurrent tasks |
| Evaluator–Optimizer | ✅ | Optional | ✅ | Iterative quality improvement |
| Orchestrator–Worker | ✅ | Optional | Optional | Task decomposition |
| Reflection | ✅ | Optional | ✅ | Self-improvement |
| ReAct | ✅ | ✅ | ✅ | Tool-using AI agents |
| Plan-and-Execute | ✅ | ✅ | Optional | Long-running complex tasks |

---

# Chapter Summary

In this chapter, we explored eight foundational workflow patterns that frequently appear in modern agentic AI systems.

These patterns provide reusable approaches for solving problems such as sequential execution, routing, parallel processing, iterative refinement, task decomposition, self-reflection, tool integration, and long-term planning.

Although these patterns can be implemented manually, frameworks such as **LangGraph** provide abstractions that make them easier to design, execute, debug, and maintain.

In the next chapter, we will begin working directly with LangGraph and learn how these workflow patterns are represented using **graphs**, **nodes**, **edges**, and **state**.