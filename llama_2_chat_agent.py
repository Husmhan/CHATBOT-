# -*- coding: utf-8 -*-
"""Llama 2 Chat Agent.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1FZzEodz3mbaXdzZzOeaaDU1Gxzxilge0
"""

!pip install -q accelerate protobuf sentencepiece torch

import pandas as pd
import os
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from huggingface_hub import login
import torch

# Hugging Face Authentication
login(token="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")

# Define the path for the CSV file
csv_file = 'qa_dataset.csv'

# Check if the CSV file exists; if not, create it with initial data
if not os.path.exists(csv_file):
    qa_data = {
        'question': ["What is the name of Julius Magellan's dog?", "Who is Julius Magellan's dog?"],
        'answer': ["The name of Julius Magellan's dog is Sparky", "Julius Magellan's dog is called Sparky"]
    }
    qa_df = pd.DataFrame(qa_data)
    qa_df.to_csv(csv_file, index=False)
else:
    # Load the existing CSV file into a DataFrame
    qa_df = pd.read_csv(csv_file)

# Verify the CSV content
qa_df = pd.read_csv(csv_file)
print(qa_df)

# Initialize the Llama 2 model and tokenizer
model_id = "NousResearch/Llama-2-7b-chat-hf"
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.use_default_system_prompt = False

# Initialize the pipeline using Hugging Face pipeline
llama_pipeline = pipeline(
    "text-generation",  # LLM task
    model=model,
    tokenizer=tokenizer,
    torch_dtype=torch.float16,
    device_map="auto",
    max_length=1024,  # Adjust max_length as needed
)

def answer_question(question):
    global qa_df
    # Check if the question is in the QA dataset
    answer = qa_df[qa_df['question'].str.lower() == question.lower()]['answer']

    if not answer.empty:
        # Return the first matching answer
        print(f"Answer from QA dataset: {answer.iloc[0]}")
    else:
        # Use Llama 2 to generate an answer
        response = llama_pipeline(question, max_length=150, do_sample=True)[0]['generated_text']

        # Ensure the response doesn't redundantly include the question or incorrectly repeat "Answer"
        response = response.replace(f"Answer: {question}", "").strip()
        print(f"Answer from Llama 2: {response}")

        # Add the new QA pair to the dataset if it's not already present
        if not any(qa_df['question'].str.lower() == question.lower()):
            new_row = pd.DataFrame({'question': [question], 'answer': [response]})
            qa_df = pd.concat([qa_df, new_row], ignore_index=True)
            qa_df.to_csv(csv_file, index=False)
            print("New QA pair added to the dataset.")

question_1 = "What is the name of Julius Magellan's dog?"
answer_question(question_1)

question_2 = "Who is Julius Magellan's dog?"
answer_question(question_2)

# This should fallback to Llama 2 and then get added
# to the dataset
question_3 = "What is the capital of France?"
answer_question(question_3)

print(qa_df)

!pip -q install gradio

import gradio as gr

def gradio_chat_interface(question):
    global qa_df
    answer = qa_df[qa_df['question'].str.lower() == question.lower()]['answer']

    if not answer.empty:
        return f"Answer from QA dataset: {answer.iloc[0]}"
    else:
        response = llama_pipeline(question, max_length=150, do_sample=True)[0]['generated_text']
        response = response.replace(f"Answer: {question}", "").strip()
        # Add new question-answer pair to the dataset
        if not any(qa_df['question'].str.lower() == question.lower()):
            new_row = pd.DataFrame({'question': [question], 'answer': [response]})
            qa_df = pd.concat([qa_df, new_row], ignore_index=True)
            qa_df.to_csv(csv_file, index=False)
            return f"Answer from Llama 2: {response} \n(New QA pair added to the dataset.)"

# Create a Gradio Interface
interface = gr.Interface(
    fn=gradio_chat_interface,
    inputs="text",
    outputs="text",
    title="Llama 2 Chatbot with QA Pipeline",
    description="Ask a question and the chatbot will respond using a pre-defined QA dataset or Llama 2 if the answer is not in the dataset.",
)

# Launch the Gradio Interface
interface.launch()

