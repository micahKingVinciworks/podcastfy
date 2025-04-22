import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import json
from openai import OpenAI
from config import OPENAI_API_KEY
from podcastfy.text_to_speech import TextToSpeech
from json_stripper import JSONStripper

class PodcastGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Podcast Generator")
        self.root.geometry("700x500")  # Further reduced size
        self.root.minsize(700, 500)  # Set minimum size
        
        # Set up OpenAI client
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Initialize JSON stripper
        self.json_stripper = JSONStripper()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="3")  # Further reduced padding
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create input area
        self.create_input_area()
        
        # Create prompt builder area
        self.create_prompt_builder()
        
        # Create TTS controls
        self.create_tts_controls()
        
        # Create output area
        self.create_output_area()
        
        # Create control buttons
        self.create_control_buttons()
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

    def create_input_area(self):
        # Input label
        ttk.Label(self.main_frame, text="Input Text:", font=('Arial', 8, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        # Input text area
        self.input_text = scrolledtext.ScrolledText(self.main_frame, width=40, height=6)  # Further reduced size
        self.input_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=1)
        
        # Add text change binding
        self.input_text.bind('<KeyRelease>', self.analyze_content)

    def create_prompt_builder(self):
        # Prompt Builder Frame
        prompt_frame = ttk.LabelFrame(self.main_frame, text="Prompt Builder", padding="3")  # Reduced padding
        prompt_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=2)
        
        # Style/Tone Selection
        ttk.Label(prompt_frame, text="Podcast Style:", font=('Arial', 8)).grid(row=0, column=0, sticky=tk.W, pady=1)
        self.style_var = tk.StringVar(value="Conversational")
        styles = ["Conversational", "Professional", "Casual", "Academic", "Humorous", "Serious"]
        style_combo = ttk.Combobox(prompt_frame, textvariable=self.style_var, values=styles, state="readonly", width=15)
        style_combo.grid(row=0, column=1, sticky=tk.W, pady=1)
        
        # Number of Speakers
        ttk.Label(prompt_frame, text="Speakers:", font=('Arial', 8)).grid(row=1, column=0, sticky=tk.W, pady=1)
        self.speakers_var = tk.StringVar(value="2")
        speakers_combo = ttk.Combobox(prompt_frame, textvariable=self.speakers_var, values=["2", "3", "4"], state="readonly", width=5)
        speakers_combo.grid(row=1, column=1, sticky=tk.W, pady=1)
        
        # Duration control
        duration_frame = ttk.Frame(prompt_frame)
        duration_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=1)
        
        ttk.Label(duration_frame, text="Duration (min):", font=('Arial', 8)).pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="5")
        self.duration_entry = ttk.Entry(duration_frame, textvariable=self.duration_var, width=3)
        self.duration_entry.pack(side=tk.LEFT, padx=2)
        
        # Duration slider
        self.duration_slider = ttk.Scale(duration_frame, from_=1, to=60, orient=tk.HORIZONTAL, 
                                       command=self.update_duration_from_slider, length=150)
        self.duration_slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.duration_slider.set(5)
        
        # Add validation for duration entry
        self.duration_var.trace_add('write', self.validate_duration)
        
        # Duration suggestion label
        self.suggestion_label = ttk.Label(prompt_frame, text="Suggested: 5 minutes", font=('Arial', 7))
        self.suggestion_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=1)

    def create_tts_controls(self):
        # TTS Controls Frame
        tts_frame = ttk.LabelFrame(self.main_frame, text="Text-to-Speech Settings", padding="10")
        tts_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # TTS Provider Selection
        ttk.Label(tts_frame, text="TTS Provider:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.tts_provider_var = tk.StringVar(value="openai")
        providers = ["openai", "elevenlabs", "edge", "gemini", "geminimulti"]
        provider_combo = ttk.Combobox(tts_frame, textvariable=self.tts_provider_var, values=providers, state="readonly")
        provider_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        provider_combo.bind('<<ComboboxSelected>>', self.update_voice_options)
        
        # Voice Selection
        ttk.Label(tts_frame, text="Host Voice:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.host_voice_var = tk.StringVar(value="echo")
        self.host_voice_combo = ttk.Combobox(tts_frame, textvariable=self.host_voice_var, state="readonly")
        self.host_voice_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(tts_frame, text="Guest Voice:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.guest_voice_var = tk.StringVar(value="shimmer")
        self.guest_voice_combo = ttk.Combobox(tts_frame, textvariable=self.guest_voice_var, state="readonly")
        self.guest_voice_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Initialize voice options
        self.update_voice_options()
        
        # Output Directory
        ttk.Label(tts_frame, text="Output Directory:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value="./output")
        ttk.Entry(tts_frame, textvariable=self.output_dir_var, width=40).grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Button(tts_frame, text="Browse", command=self.browse_output_dir).grid(row=3, column=2, padx=5)

    def update_voice_options(self, event=None):
        provider = self.tts_provider_var.get()
        if provider == "openai":
            voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        elif provider == "elevenlabs":
            voices = ["Rachel", "Domi", "Bella", "Antoni", "Josh", "Arnold", "Adam", "Sam"]
        elif provider == "edge":
            voices = ["en-US-JennyNeural", "en-US-GuyNeural", "en-US-AriaNeural", "en-US-DavisNeural"]
        elif provider == "gemini":
            voices = ["en-US-Journey-D", "en-US-Journey-F", "en-US-Journey-O"]
        else:  # geminimulti
            voices = ["R", "S", "T", "U"]
            
        self.host_voice_combo['values'] = voices
        self.guest_voice_combo['values'] = voices
        if not self.host_voice_var.get() in voices:
            self.host_voice_var.set(voices[0])
        if not self.guest_voice_var.get() in voices:
            self.guest_voice_var.set(voices[1])

    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)

    def analyze_content(self, event=None):
        """Analyze input content and suggest podcast parameters"""
        content = self.input_text.get("1.0", tk.END).strip()
        
        # Try to parse as JSON and strip if possible
        try:
            json_content = json.loads(content)
            stripped_content = self.json_stripper.strip(json_content)
            # Convert back to string for display
            content = json.dumps(stripped_content, indent=2)
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", content)
        except json.JSONDecodeError:
            # Not JSON, proceed with normal text
            pass
        
        # Calculate suggested duration based on content length
        word_count = len(content.split())
        suggested_minutes = max(5, min(60, word_count // 100))  # Adjusted to 100 words per minute for more content
        
        self.suggestion_label.config(text=f"Suggested duration: {suggested_minutes} minutes")
        self.duration_var.set(str(suggested_minutes))
        self.duration_slider.set(suggested_minutes)

    def update_duration_from_slider(self, value):
        minutes = int(float(value))
        self.duration_var.set(str(minutes))

    def validate_duration(self, *args):
        try:
            value = self.duration_var.get()
            if value:
                minutes = float(value)
                if minutes <= 0:
                    self.duration_var.set("1")
                    self.duration_slider.set(1)
                elif minutes > 60:
                    self.duration_var.set("60")
                    self.duration_slider.set(60)
                else:
                    self.duration_slider.set(minutes)
        except ValueError:
            self.duration_var.set("5")
            self.duration_slider.set(5)

    def create_output_area(self):
        # Output label
        ttk.Label(self.main_frame, text="Generated Text:", font=('Arial', 8, 'bold')).grid(row=5, column=0, sticky=tk.W)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(self.main_frame, width=40, height=8)  # Further reduced size
        self.output_text.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=1)

    def create_control_buttons(self):
        # Button Frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=2)
        
        # Generate text button
        self.generate_button = ttk.Button(button_frame, text="Generate Text", command=self.generate_podcast, width=12)
        self.generate_button.pack(side=tk.LEFT, padx=2)
        
        # Generate audio button
        self.audio_button = ttk.Button(button_frame, text="Generate Audio", command=self.generate_audio, width=12)
        self.audio_button.pack(side=tk.LEFT, padx=2)
        
        # Clear button
        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_all, width=8)
        self.clear_button.pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="", font=('Arial', 8))
        self.status_label.grid(row=8, column=0, columnspan=2)

    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.status_label.config(text="")
        self.duration_var.set("5")
        self.duration_slider.set(5)
        self.suggestion_label.config(text="Suggested duration: 5 minutes")
        self.custom_prompt.delete("1.0", tk.END)
        self.custom_prompt.insert("1.0", "You are a podcast host creating an engaging conversation about the given topic. Create a dialogue between speakers discussing the topic in an interesting and informative way.")

    def calculate_tokens(self, minutes):
        # Calculate completion tokens based on duration
        # 150 words per minute * 3 tokens per word for completion
        completion_tokens_per_minute = 150 * 3  # 450 tokens per minute
        min_completion_tokens = 1000  # Minimum completion tokens
        max_completion_tokens = 16000  # Maximum completion tokens
        calculated_completion_tokens = int(minutes * completion_tokens_per_minute)
        return min(max_completion_tokens, max(min_completion_tokens, calculated_completion_tokens))  # Ensure completion stays within limits

    def trim_content(self, content, max_tokens=8000):
        """Trim content to fit within token limits."""
        try:
            # Count tokens in the content
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": content}],
                max_tokens=1
            )
            content_tokens = response.usage.prompt_tokens
            
            if content_tokens <= max_tokens:
                return content
            
            # If content is too large, trim it proportionally
            words = content.split()
            token_ratio = content_tokens / len(words)
            target_words = int(max_tokens / token_ratio)
            trimmed_content = ' '.join(words[:target_words])
            
            return trimmed_content
        except Exception as e:
            print(f"Error trimming content: {e}")
            return content

    def generate_podcast(self):
        """Generate podcast script using OpenAI API."""
        try:
            content = self.input_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showerror("Error", "Please enter content first")
                return
            
            self.status_label.config(text="Generating podcast...")
            self.root.update()
            
            # Get parameters from GUI
            duration = int(self.duration_var.get())
            style = self.style_var.get()
            num_speakers = self.speakers_var.get()
            tts_provider = self.tts_provider_var.get()
            voice = self.host_voice_var.get()
            
            # Calculate tokens based on duration
            tokens = self.calculate_tokens(duration)
            
            # Ensure we don't exceed the model's completion token limit
            max_completion_tokens = 4096  # GPT-4's completion token limit
            if tokens > max_completion_tokens:
                self.status_label.config(text=f"Warning: Duration too long. Reducing to {max_completion_tokens} tokens.")
                tokens = max_completion_tokens
            
            # Generate podcast script
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": f"You are a podcast host creating an engaging conversational conversation.\nCreate a dialogue between {num_speakers} speakers discussing the topic in an interesting and informative way.\nThe conversation should be approximately {duration*150} words long. Please make sure that all content is covered. Add Natural pauses and breaks to the conversation. Ensure that Characters remain consistent."},
                    {"role": "user", "content": content}
                ],
                max_tokens=tokens,
                temperature=0.7
            )
            
            podcast_script = response.choices[0].message.content
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", podcast_script)
            
            # Display token usage
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            self.status_label.config(text=f"Tokens used: {total_tokens} (Prompt: {prompt_tokens}, Completion: {completion_tokens})")
            
        except Exception as e:
            error_msg = str(e)
            if "max_tokens" in error_msg:
                self.status_label.config(text="Error: Duration too long. Please reduce the duration.")
            else:
                self.status_label.config(text=f"Error: {error_msg}")

    def generate_audio(self):
        try:
            # Get the generated text
            podcast_text = self.output_text.get("1.0", tk.END).strip()
            if not podcast_text:
                self.status_label.config(text="Please generate podcast text first!")
                return
            
            # Update status
            self.status_label.config(text="Generating audio...")
            
            # Initialize TTS
            tts = TextToSpeech(
                model=self.tts_provider_var.get(),
                conversation_config={
                    "text_to_speech": {
                        "default_tts_model": self.tts_provider_var.get(),
                        self.tts_provider_var.get(): {
                            "default_voices": {
                                "question": self.host_voice_var.get(),
                                "answer": self.guest_voice_var.get()
                            }
                        }
                    }
                }
            )
            
            # Create output directory if it doesn't exist
            output_dir = self.output_dir_var.get()
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate audio file
            output_file = os.path.join(output_dir, "podcast.mp3")
            tts.convert_to_speech(podcast_text, output_file)
            
            # Update status
            self.status_label.config(text=f"Audio generated successfully! Saved to: {output_file}")
            
        except Exception as e:
            self.status_label.config(text=f"Error generating audio: {str(e)}")

def main():
    root = tk.Tk()
    app = PodcastGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 