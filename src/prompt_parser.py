import re
from typing import List, Tuple
import time

def parse_qa_pairs(response: str) -> List[Tuple[str, str]]:
    """
    Parse the Gemini response into question-answer pairs.
    
    Args:
        response: String containing Q&A pairs from Gemini
        
    Returns:
        List of tuples containing (question, answer) pairs
    """
    qa_pairs = []
    # Split response into lines and filter empty lines
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    
    for line in lines:
        # Split each line into question and answer
        q, a = line.split(';A:')
        # Remove 'Q: ' prefix from question and strip whitespace
        q = q.replace('Q:', '').strip()
        # Strip whitespace from answer
        a = a.strip()
        qa_pairs.append((q, a))
    
    return qa_pairs

def run_quiz(qa_pairs: List[Tuple[str, str]]):
    """
    Run an interactive quiz with the given Q&A pairs.
    
    Args:
        qa_pairs: List of (question, answer) tuples
    """
    score = 0
    total = len(qa_pairs)
    
    print("\n=== English Study Quiz ===\n")
    print("Type your answer and press Enter. Type 'quit' to exit.\n")
    
    for i, (question, answer) in enumerate(qa_pairs, 1):
        print(f"\nQuestion {i}/{total}:")
        print(question)
        
        user_answer = input("Your answer: ").strip().lower()
        
        if user_answer == 'quit':
            print("\nQuiz terminated early.")
            break
            
        if user_answer == answer.lower():
            print("✓ Correct!")
            score += 1
        else:
            print(f"✗ Incorrect. The correct answer is: {answer}")
        
        # Add a small delay between questions
        time.sleep(1)
    
    # Print final score
    print(f"\nQuiz completed! Your score: {score}/{total}")
    percentage = (score / total) * 100
    print(f"Percentage: {percentage:.1f}%")