import json
import tkinter as tk
from tkinter import ttk, messagebox
from Notion import get_notion_database, create_word_dataframe, get_random_pages, get_prompt
from Gemini import generate_gemini_response
from prompt_parser import parse_qa_pairs
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class EnglishStudyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("English Study App")
        self.root.geometry("800x600")
        
        # Configure grid weights to center content
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Load config
        try:
            config_path = resource_path('config.json')
            with open(config_path, 'r') as file:
                self.config = json.load(file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config.json: {str(e)}")
            self.root.destroy()
            return
        
        # Initialize variables
        self.current_question = 0
        self.score = 0
        self.qa_pairs = []
        self.total_questions = 0
        self.df = None  # Store the database DataFrame
        
        # Create frames for different pages
        self.start_frame = ttk.Frame(root, padding="20")
        self.quiz_frame = ttk.Frame(root, padding="20")
        
        # Configure frames
        self.start_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.quiz_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create widgets for both pages
        self.create_start_page()
        self.create_quiz_page()
        
        # Show start page initially
        self.show_start_page()
    
    def create_start_page(self):
        # Configure start frame grid weights
        self.start_frame.grid_columnconfigure(0, weight=1)
        self.start_frame.grid_rowconfigure(0, weight=1)  # Top space
        self.start_frame.grid_rowconfigure(1, weight=0)  # Content
        self.start_frame.grid_rowconfigure(2, weight=1)  # Bottom space
        
        # Title
        title_label = ttk.Label(
            self.start_frame,
            text="English Study App",
            font=("Arial", 24, "bold"),
            justify=tk.CENTER
        )
        title_label.grid(row=1, column=0, pady=20)
        
        # Word count selector frame
        word_count_frame = ttk.Frame(self.start_frame)
        word_count_frame.grid(row=2, column=0, pady=10)
        
        # Word count label
        ttk.Label(
            word_count_frame,
            text="Number of words:",
            font=("Arial", 12)
        ).pack(side=tk.LEFT, padx=5)
        
        # Word count spinbox
        self.word_count_var = tk.StringVar(value="5")
        self.word_count_spinbox = ttk.Spinbox(
            word_count_frame,
            from_=1,
            to=20,
            width=5,
            textvariable=self.word_count_var
        )
        self.word_count_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Start button
        self.start_button = ttk.Button(
            self.start_frame,
            text="Start Quiz",
            command=self.start_quiz_sequence,
            width=20
        )
        self.start_button.grid(row=3, column=0, pady=20)
    
    def create_quiz_page(self):
        # Configure quiz frame grid weights
        self.quiz_frame.grid_columnconfigure(0, weight=1)
        self.quiz_frame.grid_columnconfigure(1, weight=1)
        self.quiz_frame.grid_rowconfigure(0, weight=1)  # Top space
        self.quiz_frame.grid_rowconfigure(1, weight=0)  # Question label
        self.quiz_frame.grid_rowconfigure(2, weight=0)  # Answer entry
        self.quiz_frame.grid_rowconfigure(3, weight=0)  # Submit button
        self.quiz_frame.grid_rowconfigure(4, weight=0)  # Score label
        self.quiz_frame.grid_rowconfigure(5, weight=0)  # Button frame
        self.quiz_frame.grid_rowconfigure(6, weight=1)  # Bottom space
        
        # Question display
        self.question_label = ttk.Label(
            self.quiz_frame,
            text="",
            wraplength=600,
            font=("Arial", 12),
            justify=tk.CENTER
        )
        self.question_label.grid(row=1, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Answer entry
        self.answer_var = tk.StringVar()
        self.answer_entry = ttk.Entry(
            self.quiz_frame,
            textvariable=self.answer_var,
            width=40,
            font=("Arial", 12)
        )
        self.answer_entry.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Submit button
        self.submit_button = ttk.Button(
            self.quiz_frame,
            text="Submit",
            command=self.check_answer,
            width=15
        )
        self.submit_button.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Score display
        self.score_label = ttk.Label(
            self.quiz_frame,
            text="Score: 0/0",
            font=("Arial", 10),
            justify=tk.CENTER
        )
        self.score_label.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Button frame
        button_frame = ttk.Frame(self.quiz_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Configure button frame
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        # New quiz button
        self.new_quiz_button = ttk.Button(
            button_frame,
            text="New Quiz",
            command=self.start_new_quiz,
            width=15
        )
        self.new_quiz_button.grid(row=0, column=0, padx=5)
        
        # Back to start button
        self.back_button = ttk.Button(
            button_frame,
            text="Back to Start",
            command=self.show_start_page,
            width=15
        )
        self.back_button.grid(row=0, column=1, padx=5)
        
        # Reload database button
        self.reload_button = ttk.Button(
            button_frame,
            text="Reload Database",
            command=self.load_database,
            width=15
        )
        self.reload_button.grid(row=0, column=2, padx=5)
        
        # Initially disable quiz-related widgets
        self.answer_entry.config(state='disabled')
        self.submit_button.config(state='disabled')
        
        # Bind Enter key to submit
        self.answer_entry.bind('<Return>', lambda e: self.check_answer())
    
    def show_start_page(self):
        self.quiz_frame.grid_remove()
        self.start_frame.grid()
        self.start_button.config(state='normal')
    
    def show_quiz_page(self):
        self.start_frame.grid_remove()
        self.quiz_frame.grid()
    
    def start_quiz_sequence(self):
        """Start the quiz sequence by loading database first"""
        self.start_button.config(state='disabled')
        self.root.update()
        
        # Only load database if it hasn't been loaded yet
        if self.df is None:
            if self.load_database():
                self.show_quiz_page()
                self.start_new_quiz()
            else:
                self.start_button.config(state='normal')
        else:
            # If database is already loaded, just show quiz page and start quiz
            self.show_quiz_page()
            self.start_new_quiz()
    
    def load_database(self):
        """Load or reload the database from Notion"""
        try:
            # Get data from Notion database
            database = get_notion_database(
                self.config.get('NOTION_API_KEY'),
                self.config.get('NOTION_DATABASE_ID')
            )
            
            # Create DataFrame with required columns
            column_names = ['Word', 'Meaning', 'Multiplicity']
            self.df = create_word_dataframe(database, column_names)
            
            if self.df is None or self.df.empty:
                messagebox.showerror("Error", "Database is empty!")
                return False
                
            messagebox.showinfo("Success", "Database loaded successfully!")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load database: {str(e)}")
            return False
    
    def start_new_quiz(self):
        if self.df is None:
            messagebox.showerror("Error", "Database not loaded. Please reload the database.")
            return
        
        # Get number of words from spinbox
        try:
            num_words = int(self.word_count_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of words")
            return
        
        # Enable quiz-related widgets
        self.answer_entry.config(state='normal')
        self.submit_button.config(state='normal')
        
        # Get random pages
        random_words_df = get_random_pages(self.df, num_words)
        
        # Generate prompt and get response from Gemini
        prompt = get_prompt(random_words_df)
        response = generate_gemini_response(prompt, self.config.get('GEMINI_API_KEY'))
        
        # Parse Q&A pairs
        self.qa_pairs = parse_qa_pairs(response)
        self.total_questions = len(self.qa_pairs)
        self.current_question = 0
        self.score = 0
        
        # Update UI
        self.update_question()
        self.update_score()
        
        # Ensure answer entry is enabled and focused
        self.answer_entry.focus_set()
        self.answer_entry.icursor(0)
    
    def update_question(self):
        if self.current_question < self.total_questions:
            question, _ = self.qa_pairs[self.current_question]
            self.question_label.config(
                text=f"Question {self.current_question + 1}/{self.total_questions}:\n{question}"
            )
            self.answer_var.set("")
            # Ensure answer entry is enabled and focused
            self.answer_entry.config(state='normal')
            self.answer_entry.focus_set()
            self.answer_entry.icursor(0)  # Move cursor to start of entry
        else:
            self.show_final_score()
    
    def check_answer(self):
        if self.current_question >= self.total_questions:
            return
        
        user_answer = self.answer_var.get().strip().lower()
        _, correct_answer = self.qa_pairs[self.current_question]
        
        if user_answer == correct_answer.lower():
            self.score += 1
            messagebox.showinfo("Correct!", "✓ Well done!")
        else:
            messagebox.showerror(
                "Incorrect",
                f"✗ The correct answer is: {correct_answer}"
            )
        
        self.current_question += 1
        self.update_score()
        self.update_question()
    
    def update_score(self):
        self.score_label.config(
            text=f"Score: {self.score}/{self.current_question}"
        )
    
    def show_final_score(self):
        percentage = (self.score / self.total_questions) * 100
        messagebox.showinfo(
            "Quiz Completed!",
            f"Final Score: {self.score}/{self.total_questions}\n"
            f"Percentage: {percentage:.1f}%"
        )
        self.question_label.config(text="Click 'New Quiz' to start another quiz!")

def main():
    root = tk.Tk()
    app = EnglishStudyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 