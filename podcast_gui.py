import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import os
from openai import OpenAI
from config import OPENAI_API_KEY
from podcastfy.text_to_speech import TextToSpeech

class PodcastGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Podcast Generator")
        self.root.geometry("1000x800")
        
        # Set up OpenAI client
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
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
        ttk.Label(self.main_frame, text="Input Text:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        # Input text area
        self.input_text = scrolledtext.ScrolledText(self.main_frame, width=60, height=10)
        self.input_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Add text change binding
        self.input_text.bind('<KeyRelease>', self.analyze_content)

    def create_prompt_builder(self):
        # Prompt Builder Frame
        prompt_frame = ttk.LabelFrame(self.main_frame, text="Prompt Builder", padding="10")
        prompt_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Style/Tone Selection
        ttk.Label(prompt_frame, text="Podcast Style:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.style_var = tk.StringVar(value="Conversational")
        styles = ["Conversational", "Professional", "Casual", "Academic", "Humorous", "Serious"]
        style_combo = ttk.Combobox(prompt_frame, textvariable=self.style_var, values=styles, state="readonly")
        style_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Number of Speakers
        ttk.Label(prompt_frame, text="Number of Speakers:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.speakers_var = tk.StringVar(value="2")
        speakers_combo = ttk.Combobox(prompt_frame, textvariable=self.speakers_var, values=["2", "3", "4"], state="readonly")
        speakers_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Duration control
        duration_frame = ttk.Frame(prompt_frame)
        duration_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(duration_frame, text="Duration (minutes):").pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="5")
        self.duration_entry = ttk.Entry(duration_frame, textvariable=self.duration_var, width=5)
        self.duration_entry.pack(side=tk.LEFT, padx=5)
        
        # Duration slider
        self.duration_slider = ttk.Scale(duration_frame, from_=1, to=60, orient=tk.HORIZONTAL, 
                                       command=self.update_duration_from_slider)
        self.duration_slider.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.duration_slider.set(5)
        
        # Add validation for duration entry
        self.duration_var.trace_add('write', self.validate_duration)
        
        # Duration suggestion label
        self.suggestion_label = ttk.Label(prompt_frame, text="Suggested duration: 5 minutes", font=('Arial', 8))
        self.suggestion_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Custom System Prompt
        ttk.Label(prompt_frame, text="Custom System Prompt:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.custom_prompt = scrolledtext.ScrolledText(prompt_frame, width=50, height=3)
        self.custom_prompt.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        self.custom_prompt.insert("1.0", "You are a podcast host creating an engaging conversation about the given topic. Create a dialogue between speakers discussing the topic in an interesting and informative way.")

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
        content = self.input_text.get("1.0", tk.END).strip()
        if not content:
            return
            
        try:
            # Count words and estimate complexity
            words = len(content.split())
            sentences = len([s for s in content.split('.') if s.strip()])
            paragraphs = len([p for p in content.split('\n\n') if p.strip()])
            
            # More accurate estimation:
            # - Base rate: 100 words per minute for conversational content
            # - Adjust for complexity (more complex = slower pace)
            # - Consider paragraph structure (more paragraphs = more natural breaks)
            complexity_factor = min(2.0, max(0.8, sentences / (words / 15)))  # Normalize sentences per 15 words
            paragraph_factor = min(1.5, max(1.0, paragraphs / (sentences / 3)))  # Normalize paragraphs per 3 sentences
            
            # Calculate base duration
            base_minutes = words / 100  # 100 words per minute base rate
            
            # Apply complexity and paragraph factors
            suggested_minutes = base_minutes * complexity_factor * paragraph_factor
            
            # Round to nearest minute and ensure within bounds
            suggested_minutes = max(1, min(60, round(suggested_minutes)))
            
            # Update suggestion and current duration
            self.suggestion_label.config(text=f"Suggested duration: {suggested_minutes} minutes")
            self.duration_var.set(str(suggested_minutes))
            self.duration_slider.set(suggested_minutes)
            
        except Exception as e:
            print(f"Error analyzing content: {e}")

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
        ttk.Label(self.main_frame, text="Generated Podcast Text:", font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky=tk.W)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(self.main_frame, width=60, height=15)
        self.output_text.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

    def create_control_buttons(self):
        # Button Frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        # Generate text button
        self.generate_button = ttk.Button(button_frame, text="Generate Podcast Text", command=self.generate_podcast)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        # Generate audio button
        self.audio_button = ttk.Button(button_frame, text="Generate Audio", command=self.generate_audio)
        self.audio_button.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="")
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
        # Approximate tokens per minute for conversational content
        tokens_per_minute = 150
        return int(minutes * tokens_per_minute)

    def generate_podcast(self):
        # Get input text
        input_text = self.input_text.get("1.0", tk.END).strip()
        
        if not input_text:
            self.status_label.config(text="Please enter some text first!")
            return
        
        try:
            # Update status
            self.status_label.config(text="Generating podcast text...")
            
            # Get duration and calculate tokens
            minutes = float(self.duration_var.get())
            max_tokens = self.calculate_tokens(minutes)
            
            # Build system prompt based on selections
            style = self.style_var.get()
            speakers = self.speakers_var.get()
            custom_prompt = self.custom_prompt.get("1.0", tk.END).strip()
            
            # Generate podcast using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": custom_prompt},
                    {"role": "user", "content": f"Create a {style.lower()} podcast transcript with {speakers} speakers about: {input_text}. The transcript should be approximately {minutes} minutes long when spoken at a natural pace."}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            # Get the generated text
            podcast_text = response.choices[0].message.content
            
            # Update output area
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", podcast_text)
            
            # Update status
            self.status_label.config(text=f"Podcast text generated successfully! (Target duration: {minutes} minutes)")
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")

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