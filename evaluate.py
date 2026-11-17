import os
from dotenv import load_dotenv
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
)

from rag_engine import ask_rag

# Load OPENAI_API_KEY so DeepEval can use OpenAI as its evaluation judge
load_dotenv()

# 1. Define golden evaluation test cases based on your uploaded TN Agriculture PDF
# (Feel free to add more questions & expected answers from your specific PDF!)
eval_dataset = [
    {
        "question": "What is the subsidy percentage for pulses seed farms?",
        "expected_output": "The subsidy percentage for pulses seed farms is 24% for SC/ST farmers and 20% for Farm Women, subject to availability of funds."
    },
    {
        "question": "Who is eligible to avail the subsidy for raising seed farms with Pulses crop?",
        "expected_output": "All farmers who raise seed farms with Pulses crop are eligible to avail the subsidy subject to availability of funds."
    }
]


def run_evaluation():
    print("Running RAG pipeline on test questions...\n")
    test_cases = []

    for item in eval_dataset:
        question = item["question"]
        expected = item["expected_output"]

        # Call our actual FAISS + LangChain RAG engine
        rag_result = ask_rag(question)
        actual_answer = rag_result["answer"]
        retrieved_contexts = rag_result["contexts"]

        print(f"Question : {question}")
        print(f"Bot Reply: {actual_answer}")
        print(f"Chunks Retrieved: {len(retrieved_contexts)}\n" + "-" * 60)

        # Create a DeepEval LLMTestCase
        test_case = LLMTestCase(
            input=question,
            actual_output=actual_answer,
            expected_output=expected,
            retrieval_context=retrieved_contexts
        )
        test_cases.append(test_case)

    # 2. Configure DeepEval Metrics (using gpt-4o-mini as the judge to keep costs low)
    faithfulness = FaithfulnessMetric(
        threshold=0.7,
        model="gpt-4o-mini",
        include_reason=True
    )
    answer_relevancy = AnswerRelevancyMetric(
        threshold=0.7,
        model="gpt-4o-mini",
        include_reason=True
    )
    contextual_precision = ContextualPrecisionMetric(
        threshold=0.7,
        model="gpt-4o-mini",
        include_reason=True
    )

    # 3. Execute evaluation and print detailed scorecard
    print("\nStarting DeepEval Metric Scoring...\n")
    evaluate(
        test_cases=test_cases,
        metrics=[faithfulness, answer_relevancy, contextual_precision]
    )


if __name__ == "__main__":
    run_evaluation()