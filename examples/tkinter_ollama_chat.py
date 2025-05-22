#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Tkinter interface for chat with Ollama LLM with speech recognition and synthesis
"""

import os
import sys
import time
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, simpledialog, messagebox
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# Set environment variables to disable camera module initialization and force CPU-only processing
os.environ["WITCH_DISABLE_CAMERA"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Disable CUDA
os.environ["TORCH_DEVICE"] = "cpu"       # Force PyTorch to use CPU
os.environ["USE_CPU_ONLY"] = "1"         # Generic flag for CPU-only mode

# Add parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import witch-core modules using core functions
from src.llm.ollama_chat_manager import OllamaChatManager
from src.llm.conversation import ConversationHistory

# Import only the specific audio modules needed
import importlib.util
# Manually import the specific modules we need without triggering full package initialization
if importlib.util.find_spec("src.io.audio.tts"):
    from src.io.audio.tts import TTSManager, get_tts_manager  # Using the core TTS functionality
if importlib.util.find_spec("src.io.audio.asr"):
    from src.io.audio.asr import get_recording_manager  # Using the core ASR functionality
if importlib.util.find_spec("src.io.audio.language_utils"):
    from src.io.audio.language_utils import (
        SUPPORTED_LANGUAGES, get_language_code, 
        get_voice_for_language, detect_preferred_language
    )  # Using the core language utilities

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_tkinter_ollama.log')
    ]
)

logger = logging.getLogger(__name__)
logger.info("Script starting up")

# Flag to track Whisper availability
try:
    import whisper
    WHISPER_AVAILABLE = True
    logger.info("Whisper imported successfully")
except ImportError:
    logger.warning("Whisper not found. Voice recognition will be disabled.")
    WHISPER_AVAILABLE = False

# Flag to track TTS availability
TTS_AVAILABLE = True  # We'll use witch-core TTS regardless of pyttsx3

# ASR and TTS functionality now directly uses the core functions from the imported modules


class OllamaChatApp:
    """Tkinter application for chat with Ollama LLM with speech recognition and synthesis"""
    
    # Default ASR models list
    WHISPER_MODELS = [
        "tiny",
        "base",
        "small",
        "medium",
        "large",
    ]
    
    # Available TTS engines - all MIT license compatible
    TTS_ENGINES = [
        "auto",         # Auto-detect best TTS engine
        "pyttsx",       # System TTS (pyttsx3)
        "gtts",         # Google TTS
        "enhanced_gtts", # Google TTS with language detection
        "espeak",       # eSpeak TTS
        "festival",     # Festival TTS
    ]
    
    # Use the language list from core if available, otherwise fallback
    try:
        LANGUAGES = SUPPORTED_LANGUAGES
    except NameError:
        # Fallback language list if core utility isn't available
        LANGUAGES = [
            "auto",        # Auto-detect (only for TTS with enhanced_gtts)
            "en",          # English
            "ja",          # Japanese
            "zh-cn",       # Chinese (Simplified)
            "zh-tw",       # Chinese (Traditional)
            "ko",          # Korean
            "fr",          # French
            "de",          # German
            "es",          # Spanish
            "it",          # Italian
            "ru",          # Russian
            "pt",          # Portuguese
            "nl",          # Dutch
            "pl",          # Polish
        ]
    
    def __init__(self, root):
        logger.info("Initializing OllamaChatApp")
        self.root = root
        self.root.title("Ollama Chat")
        # More compact size for old-style window application
        self.root.geometry("600x450")
        
        # Set minimum window size
        self.root.minsize(500, 350)
        
        # Initialize variables
        self.recording_manager = None
        self.text_to_speech = None
        self.is_recording = False
        self.enable_tts = False
        self.tts_engine = "auto"  # Default TTS engine
        self.is_streaming = False
        
        # System prompt for the LLM to ensure plain text responses
        self.system_prompt = (
            "Please respond with plain text only. Do not use special characters, "
            "markdown formatting, code blocks, or other formatting that may interfere "
            "with text display or speech synthesis. Keep responses concise and readable."
        )
        
        # Create microphone icons (normal and recording state)
        self.mic_normal_img = tk.PhotoImage(data='''
        R0lGODlhEAAQAIAAAP///wAAACH5BAAAAAAALAAAAAAQABAAAAIgjI+py+0Po5y02ouz3rz7D4biSJbmiabqyrbuC8fyTAA
        AO''')
        self.mic_recording_img = tk.PhotoImage(data='''
        R0lGODlhEAAQAIABAP8AAAAAACH5BAAAAAAALAAAAAAQABAAAAIgjI+py+0Po5y02ouz3rz7D4biSJbmiabqyrbuC8fyTAA
        AO''')
        
        # Configure style for an old Windows look
        self.configure_old_windows_style()
        
        # Create status bar FIRST to ensure it appears at the bottom of the window
        self.create_status_bar()
        
        # Create main frame with minimal padding that will contain all UI components
        self.main_frame = ttk.Frame(self.root, padding="3")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.columnconfigure(0, weight=1)  # Make the column expandable
        self.main_frame.rowconfigure(1, weight=1)    # Make the chat row expandable
        
        # Row 0: Settings area (fixed height)
        self.create_settings_frame()
        
        # Row 1: Chat display (expandable)
        self.create_chat_display()
        
        # Row 2: Input area (fixed height)
        self.create_input_area()
        
        # Initialize Ollama Chat Manager from the core
        self.ollama_chat_manager = None
        self.initialize_ollama_manager()
        
        # Initialize audio components if available
        self.initialize_audio_components()
        
        # Update status
        self.update_status("Ready")
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("OllamaChatApp initialization complete")
    
    def configure_old_windows_style(self):
        """Configure the application style to look like an old Windows application"""
        style = ttk.Style()
        
        # Use the classic theme if available
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        # Configure a more compact, old-school look
        style.configure('TButton', font=('Arial', 8))
        style.configure('TLabel', font=('Arial', 8))
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabelframe', background='#f0f0f0', font=('Arial', 8))
        style.configure('TLabelframe.Label', font=('Arial', 8, 'bold'))
        style.configure('TCombobox', font=('Arial', 8))
        style.configure('TCheckbutton', font=('Arial', 8))
        
        # Microphone button styles
        style.configure("Mic.Normal.TButton", padding=2)
        style.configure("Mic.Active.TButton", padding=2, background='#ff9999')
        
        # Status bar style
        style.configure("Status.TLabel", relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 8))
    
    def create_settings_frame(self):
        """Create the top frame with model selection and settings"""
        settings_frame = ttk.Frame(self.main_frame)
        settings_frame.grid(row=0, column=0, sticky="ew", pady=2)
        
        # Ollama model selection - more compact
        ollama_frame = ttk.LabelFrame(settings_frame, text="Model")
        ollama_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        ttk.Label(ollama_frame, text="Model:").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.model_var = tk.StringVar(value="") # Will be populated from available models
        self.model_combo = ttk.Combobox(ollama_frame, textvariable=self.model_var, width=10)
        self.model_combo.grid(row=0, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)
        
        # Refresh models button
        self.refresh_models_button = ttk.Button(
            ollama_frame,
            text="⟳",
            command=self.refresh_models,
            width=2
        )
        self.refresh_models_button.grid(row=0, column=2, padx=2, pady=2)
        
        ttk.Label(ollama_frame, text="Temp:").grid(row=0, column=3, padx=2, pady=2, sticky=tk.W)
        self.temperature_var = tk.DoubleVar(value=0.7)
        temperature_scale = ttk.Scale(ollama_frame, from_=0.0, to=1.0, variable=self.temperature_var, length=70)
        temperature_scale.grid(row=0, column=4, padx=2, pady=2, sticky=(tk.W, tk.E))
        temperature_scale.bind("<ButtonRelease-1>", self.on_temperature_change)
        
        # Speech settings - more compact
        speech_frame = ttk.LabelFrame(settings_frame, text="Speech")
        speech_frame.pack(side=tk.RIGHT, fill=tk.X, padx=2)
        
        # Whisper model selection
        ttk.Label(speech_frame, text="ASR:").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.whisper_model_var = tk.StringVar(value="tiny")
        whisper_combo = ttk.Combobox(speech_frame, textvariable=self.whisper_model_var, values=self.WHISPER_MODELS, width=6)
        whisper_combo.grid(row=0, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))
        whisper_combo.bind("<<ComboboxSelected>>", self.on_whisper_model_change)
        
        # TTS settings
        ttk.Label(speech_frame, text="TTS:").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.tts_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(speech_frame, text="Enable", variable=self.tts_var, command=self.toggle_tts).grid(
            row=1, column=1, padx=2, pady=2, sticky=tk.W)
        
        # TTS engine selection
        self.tts_engine_var = tk.StringVar(value=self.TTS_ENGINES[0])
        tts_engine_combo = ttk.Combobox(speech_frame, textvariable=self.tts_engine_var, values=self.TTS_ENGINES, width=10)
        tts_engine_combo.grid(row=1, column=2, padx=2, pady=2, sticky=(tk.W, tk.E))
        tts_engine_combo.bind("<<ComboboxSelected>>", self.on_tts_engine_change)
        
        # Language settings
        language_frame = ttk.LabelFrame(settings_frame, text="Language")
        language_frame.pack(side=tk.RIGHT, fill=tk.X, padx=2)
        
        # ASR language selection
        ttk.Label(language_frame, text="ASR Lang:").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.asr_language_var = tk.StringVar(value="en")
        asr_language_combo = ttk.Combobox(language_frame, textvariable=self.asr_language_var, values=self.LANGUAGES, width=6)
        asr_language_combo.grid(row=0, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))
        asr_language_combo.bind("<<ComboboxSelected>>", self.on_asr_language_change)
        
        # TTS language selection
        ttk.Label(language_frame, text="TTS Lang:").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.tts_language_var = tk.StringVar(value="en")
        tts_language_combo = ttk.Combobox(language_frame, textvariable=self.tts_language_var, values=self.LANGUAGES, width=6)
        tts_language_combo.grid(row=1, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))
        tts_language_combo.bind("<<ComboboxSelected>>", self.on_tts_language_change)
    
    def create_chat_display(self):
        """Create the middle frame with chat display"""
        # Create chat display
        chat_frame = ttk.Frame(self.main_frame)
        chat_frame.grid(row=1, column=0, sticky="nsew", pady=2)
        
        # Use a monospace font for classic look
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, font=("Courier New", 9))
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Add tag for bold text
        self.chat_display.tag_configure("bold", font=("Courier New", 9, "bold"))
    
    def create_input_area(self):
        """Create the bottom frame with input area"""
        input_frame = ttk.Frame(self.main_frame)
        input_frame.grid(row=2, column=0, sticky="ew", pady=2)
        
        # Button frame to ensure buttons are always visible
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Message input - now with reduced width to leave room for buttons
        self.message_input = ttk.Entry(input_frame, font=("Courier New", 9))
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_input.bind("<Return>", lambda event: self.send_message())
        
        # Microphone button with fixed width
        self.mic_button = ttk.Button(
            button_frame, 
            image=self.mic_normal_img,
            command=self.toggle_recording,
            style="Mic.Normal.TButton",
            width=3
        )
        self.mic_button.pack(side=tk.LEFT, padx=2, pady=2)
        if not WHISPER_AVAILABLE:
            self.mic_button.config(state=tk.DISABLED)
        
        # Send button with fixed width
        self.send_button = ttk.Button(
            button_frame, 
            text="Send", 
            command=self.send_message,
            width=5
        )
        self.send_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Clear button with fixed width
        self.clear_button = ttk.Button(
            button_frame, 
            text="Clear", 
            command=self.clear_chat,
            width=5
        )
        self.clear_button.pack(side=tk.LEFT, padx=2, pady=2)
    
    def create_status_bar(self):
        """Create a status bar at the bottom of the window"""
        # Create a frame at the bottom of the root window
        self.status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create the status label
        self.status_label = ttk.Label(self.status_frame, text="Ready", anchor=tk.W, 
                                     font=("Arial", 8), style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=2)
    
    def update_status(self, message):
        """Update the status bar message"""
        self.status_label.config(text=message)
        # Force update the UI to ensure the status is visible immediately
        self.root.update_idletasks()
        logger.debug(f"Status: {message}")
    
    def initialize_ollama_manager(self):
        """Initialize Ollama chat manager from the core library"""
        try:
            # Create OllamaChatManager with status updates sent to the UI
            self.ollama_chat_manager = OllamaChatManager(
                host="localhost", 
                port=11434,
                system_prompt=self.system_prompt,
                status_callback=self.update_status
            )
            
            # Check if manager is available
            if not self.ollama_chat_manager.is_available():
                logger.error("Ollama manager is not available")
                self.update_status("Error: Ollama not available")
                return False
                
            # Get list of models and update the UI
            available_models = self.ollama_chat_manager.get_available_models()
            logger.info(f"Available models: {available_models}")
            
            # Update model combobox
            self.model_combo["values"] = available_models
            
            # Set initial model selection
            if available_models:
                current_model = self.ollama_chat_manager.get_current_model()
                if current_model:
                    self.model_var.set(current_model)
                    logger.info(f"Selected model: {current_model}")
                else:
                    self.model_var.set(available_models[0])
                    self.ollama_chat_manager.set_model(available_models[0])
                    logger.info(f"Selected first available model: {available_models[0]}")
            
            # Set up streaming UI with our text widget
            self.ollama_chat_manager.setup_streaming_ui(
                text_widget=self.chat_display,
                root_window=self.root,
                end_marker=tk.END,
                bold_tag="bold",
                sender_name="Ollama"
            )
            
            logger.info("Ollama chat manager initialized successfully")
            self.update_status("Ollama initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Ollama chat manager: {e}")
            self.update_status(f"Error initializing Ollama: {str(e)}")
            return False
    
    def refresh_models(self):
        """Refresh the list of available models"""
        try:
            self.update_status("Refreshing models...")
            
            # Use the core manager to refresh models
            if self.ollama_chat_manager:
                models = self.ollama_chat_manager.refresh_models()
                
                if models:
                    # Update the combobox with new model list
                    self.model_combo["values"] = models
                    
                    # Keep current selection if it still exists
                    current_model = self.model_var.get()
                    if current_model not in models and models:
                        # Select first available model if current is no longer available
                        self.model_var.set(models[0])
                        self.ollama_chat_manager.set_model(models[0])
                        
                    self.update_status(f"Found {len(models)} models")
                else:
                    self.update_status("No models found")
        except Exception as e:
            logger.error(f"Error refreshing models: {e}")
            self.update_status(f"Error refreshing models: {str(e)}")
    
    def on_model_change(self, event=None):
        """Handle change in model selection"""
        if not self.ollama_chat_manager:
            return
            
        selected_model = self.model_var.get()
        self.update_status(f"Changing model to {selected_model}...")
        
        # Use the core manager to set the model
        if self.ollama_chat_manager.set_model(selected_model):
            self.update_status(f"Model set to {selected_model}")
        else:
            self.update_status(f"Failed to set model to {selected_model}")
    
    def on_temperature_change(self, event=None):
        """Handle change in temperature setting"""
        if not self.ollama_chat_manager:
            return
            
        temp = self.temperature_var.get()
        self.ollama_chat_manager.set_temperature(temp)
        logger.info(f"Temperature set to {temp}")
    
    def initialize_audio_components(self):
        """Initialize audio components if available"""
        try:
            # Initialize recording manager from the core ASR module
            if WHISPER_AVAILABLE:
                model_name = self.whisper_model_var.get()
                # Use the UI-friendly recording manager for better integration
                self.recording_manager = get_recording_manager(
                    model_name=model_name, 
                    ui_friendly=True
                )
                
                if self.recording_manager:
                    # Set up the status update callback
                    self.recording_manager.set_status_callback(self.update_status)
                    
                    # Set up the transcription complete callback
                    self.recording_manager.on_transcription_complete = self.on_transcription_complete
                    
                    # Set up icons if we're using the UI-friendly version
                    if hasattr(self.recording_manager, "set_icons"):
                        self.recording_manager.set_icons(
                            idle_icon=self.mic_normal_img,
                            recording_icon=self.mic_recording_img
                        )
                    
                    # Set initial language
                    if hasattr(self.recording_manager, "set_language"):
                        self.recording_manager.set_language(self.asr_language_var.get())
                    
                    logger.info(f"Recording manager initialized with model {model_name}")
                else:
                    logger.warning("Recording manager initialization failed")
            
            # Initialize TTS engine from the core TTS module
            self.initialize_tts_engine()
            
            self.update_status("Audio components ready")
        except Exception as e:
            logger.error(f"Failed to initialize audio components: {e}")
            self.update_status("Error: Audio initialization failed")
    
    def initialize_tts_engine(self):
        """Initialize the selected TTS engine using core functionality"""
        if not TTS_AVAILABLE:
            logger.warning("TTS is not available")
            return
            
        try:
            engine_name = self.tts_engine_var.get() if hasattr(self, 'tts_engine_var') else "auto"
            self.tts_engine = engine_name
            
            # Initialize the TTS manager with the selected engine directly from core
            self.text_to_speech = get_tts_manager(provider_type=engine_name)
            
            if self.text_to_speech and self.text_to_speech.is_available():
                logger.info(f"Initialized TTS engine: {self.text_to_speech.provider_type}")
            else:
                logger.warning("TTS engine initialization failed or no provider available")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.update_status("TTS initialization failed")
    
    def toggle_tts(self):
        """Toggle text-to-speech on/off"""
        self.enable_tts = self.tts_var.get()
        status = "enabled" if self.enable_tts else "disabled"
        logger.info(f"TTS {status}")
        self.update_status(f"Text-to-speech {status}")
    
    def on_tts_engine_change(self, event=None):
        """Handle change in TTS engine selection"""
        new_engine = self.tts_engine_var.get()
        if new_engine != self.tts_engine:
            logger.info(f"Changing TTS engine from {self.tts_engine} to {new_engine}")
            self.tts_engine = new_engine
            self.initialize_tts_engine()
            self.update_status(f"TTS engine changed to {new_engine}")
    
    def on_whisper_model_change(self, event=None):
        """Handle change in Whisper model selection"""
        if self.recording_manager:
            # Re-initialize recording manager with new model
            model_name = self.whisper_model_var.get()
            logger.info(f"Changing Whisper model to {model_name}")
            self.recording_manager = get_recording_manager(
                model_name=model_name, 
                ui_friendly=True
            )
            
            if self.recording_manager:
                # Set up the status update callback
                self.recording_manager.set_status_callback(self.update_status)
                
                # Set up the transcription complete callback
                self.recording_manager.on_transcription_complete = self.on_transcription_complete
                
                # Set up icons if we're using the UI-friendly version
                if hasattr(self.recording_manager, "set_icons"):
                    self.recording_manager.set_icons(
                        idle_icon=self.mic_normal_img,
                        recording_icon=self.mic_recording_img
                    )
                
                self.update_status(f"ASR model changed to {model_name}")
            else:
                self.update_status(f"Failed to initialize ASR with model {model_name}")
    
    def on_asr_language_change(self, event=None):
        """Handle change in ASR language selection"""
        new_language = self.asr_language_var.get()
        if self.recording_manager and hasattr(self.recording_manager, "set_language"):
            self.recording_manager.set_language(new_language)
        logger.info(f"ASR language changed to {new_language}")
        self.update_status(f"ASR language set to {new_language}")
    
    def on_tts_language_change(self, event=None):
        """Handle change in TTS language selection"""
        new_language = self.tts_language_var.get()
        logger.info(f"TTS language changed to {new_language}")
        self.update_status(f"TTS language set to {new_language}")
    
    def toggle_recording(self):
        """Toggle audio recording on/off"""
        if not WHISPER_AVAILABLE or not self.recording_manager:
            self.update_status("Speech recognition is not available")
            return
            
        if not self.is_recording:
            # Start recording
            self.start_recording()
        else:
            # Stop recording
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio using the core ASR manager"""
        if self.is_recording:
            return False
            
        # Use the core recording manager's functionality
        if self.recording_manager and self.recording_manager.start_recording():
            self.is_recording = True
            
            # Update button appearance
            if hasattr(self.recording_manager, "get_current_icon") and self.recording_manager.get_current_icon():
                self.mic_button.configure(image=self.recording_manager.get_current_icon(), style="Mic.Active.TButton")
            else:
                self.mic_button.configure(image=self.mic_recording_img, style="Mic.Active.TButton")
            
            return True
        
        logger.error("Failed to start recording")
        return False
    
    def stop_recording(self):
        """Stop recording audio and process it using the core ASR manager"""
        if not self.is_recording:
            return False
        
        # Use the core recording manager's functionality
        if self.recording_manager and self.recording_manager.stop_recording():
            self.is_recording = False
            
            # Update button appearance
            if hasattr(self.recording_manager, "get_current_icon") and self.recording_manager.get_current_icon():
                self.mic_button.configure(image=self.recording_manager.get_current_icon(), style="Mic.Normal.TButton")
            else:
                self.mic_button.configure(image=self.mic_normal_img, style="Mic.Normal.TButton")
            
            return True
        
        logger.error("Failed to stop recording")
        return False
    
    def on_transcription_complete(self, text):
        """Callback when transcription is complete"""
        if text:
            # Set the transcribed text in the input box
            self.message_input.delete(0, tk.END)
            self.message_input.insert(0, text)
            
            # Auto-send if not empty
            if text.strip():
                self.send_message()
    
    def add_message(self, text, sender="You"):
        """Add a message to the chat display"""
        # Enable the text widget for editing
        self.chat_display.config(state=tk.NORMAL)
        
        # Insert timestamp
        timestamp = time.strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] ")
        
        # Insert sender with bold formatting
        self.chat_display.insert(tk.END, f"{sender}: ", "bold")
        
        # Insert message text
        self.chat_display.insert(tk.END, f"{text}\n\n")
        
        # Scroll to the bottom
        self.chat_display.see(tk.END)
        
        # Disable editing again
        self.chat_display.config(state=tk.DISABLED)
    
    def send_message(self):
        """Send a message to the LLM and display the response"""
        # Get message from input box
        message = self.message_input.get().strip()
        
        if not message:
            return
            
        # Clear the input box
        self.message_input.delete(0, tk.END)
        
        # Add user message to chat
        self.add_message(message, "You")
        
        # Check if Ollama manager is available
        if not self.ollama_chat_manager or not self.ollama_chat_manager.is_available():
            self.add_message("Ollama is not available. Please check that it's running.", "System")
            return
            
        # Update status
        self.update_status("Generating response...")
        
        # Disable send button to prevent multiple requests
        self.send_button.config(state=tk.DISABLED)
        
        # Prepare the chat manager for streaming
        self.ollama_chat_manager.prepare_streaming()
        
        # Use the core chat manager to handle the message and get response
        def on_response_complete(response_text):
            # Re-enable send button
            self.send_button.config(state=tk.NORMAL)
            
            # If TTS is enabled, speak the response
            if self.enable_tts and response_text and self.text_to_speech and self.text_to_speech.is_available():
                self.update_status("Speaking...")
                threading.Thread(target=self.speak_text, args=(response_text,), daemon=True).start()
        
        # Send the message using the core chat manager
        self.ollama_chat_manager.send_message(
            message=message,
            use_conversation_history=True,
            callback_on_complete=on_response_complete
        )
    
    def speak_text(self, text):
        """Convert text to speech using the core TTS functionality"""
        try:
            # Use core TTS functionality for text cleaning and speech
            logger.info(f"Speaking with engine: {self.tts_engine}, language: {self.tts_language_var.get()}, text: {text[:50]}...")
            
            # Important: TTS engine may have changed, so we must re-initialize it
            current_engine = self.tts_engine_var.get()
            if not self.text_to_speech or self.text_to_speech.provider_type != current_engine:
                logger.info(f"TTS engine needs reinitialization: current={self.text_to_speech.provider_type if self.text_to_speech else 'None'}, requested={current_engine}")
                self.tts_engine = current_engine
                # Force creation of a new instance
                self.text_to_speech = None
                self.initialize_tts_engine()
                logger.info(f"Re-initialized TTS engine to: {self.text_to_speech.provider_type if self.text_to_speech else 'None'}")
            
            # Use the core TTS manager directly
            if self.text_to_speech and self.text_to_speech.is_available():
                self.update_status(f"Speaking with {self.tts_engine} in {self.tts_language_var.get()}...")
                
                # Set the voice/language for the TTS engine based on provider type
                language = self.tts_language_var.get()
                
                # Process optimally for each provider type
                if self.text_to_speech.provider_type == "enhanced_gtts":
                    # For enhanced_gtts, we can control auto-detection
                    auto_detect = language == "auto"
                    if hasattr(self.text_to_speech._provider, "set_auto_detect"):
                        logger.info(f"Setting auto-detect for enhanced_gtts: {auto_detect}")
                        self.text_to_speech._provider.set_auto_detect(auto_detect)
                    
                    if not auto_detect:
                        # Set language directly for enhanced_gtts
                        if hasattr(self.text_to_speech._provider, "language"):
                            logger.info(f"Setting language for enhanced_gtts: {language}")
                            self.text_to_speech._provider.language = language
                    
                    success = self.text_to_speech.speak(text)
                    
                elif self.text_to_speech.provider_type == "gtts":
                    # GTTS provider requires direct language setting
                    if language != "auto":
                        logger.info(f"Setting language for gtts: {language}")
                        if hasattr(self.text_to_speech._provider, "language"):
                            self.text_to_speech._provider.language = language
                    success = self.text_to_speech.speak(text)
                    
                elif self.text_to_speech.provider_type == "pyttsx":
                    # For pyttsx3, select the appropriate voice
                    if language != "auto":
                        voices = self.text_to_speech.get_available_voices()
                        if 'get_voice_for_language' in globals():
                            voice_id = get_voice_for_language(voices, language)
                            if voice_id:
                                logger.info(f"Setting pyttsx voice to {voice_id} for {language}")
                                self.text_to_speech.set_voice(voice_id)
                        else:
                            # Fallback to basic language matching
                            for voice in voices:
                                voice_lang = str(voice.get('language', '')).lower()
                                if language in voice_lang:
                                    logger.info(f"Setting pyttsx voice to {voice['id']} for {language}")
                                    self.text_to_speech.set_voice(voice['id'])
                                    break
                    success = self.text_to_speech.speak(text)
                    
                elif self.text_to_speech.provider_type in ["espeak", "festival"]:
                    # espeak and festival allow direct language/voice setting
                    if language != "auto":
                        logger.info(f"Setting language/voice for {self.text_to_speech.provider_type}: {language}")
                        # In most cases, language codes can be used as voice IDs
                        self.text_to_speech.set_voice(language)
                    success = self.text_to_speech.speak(text)
                    
                else:
                    # General case for other providers
                    if language != "auto":
                        voices = self.text_to_speech.get_available_voices()
                        if 'get_voice_for_language' in globals():
                            voice_id = get_voice_for_language(voices, language)
                            if voice_id:
                                logger.info(f"Setting voice to {voice_id} for language {language}")
                                self.text_to_speech.set_voice(voice_id)
                        else:
                            # Fallback to basic language matching
                            for voice in voices:
                                if language in str(voice.get('language', '')).lower():
                                    logger.info(f"Setting voice to {voice['id']} for language {language}")
                                    self.text_to_speech.set_voice(voice['id'])
                                    break
                    success = self.text_to_speech.speak(text)
                
                self.update_status("Ready" if success else "TTS failed")
                return success
            else:
                self.update_status("TTS not available")
                return False
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            self.update_status("TTS error")
            return False
    
    def clear_chat(self):
        """Clear the chat display and conversation history"""
        # Clear the chat display
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Clear the conversation history in the manager
        if self.ollama_chat_manager:
            self.ollama_chat_manager.clear_conversation()
            
        self.update_status("Chat cleared")
    
    def on_closing(self):
        """Clean up resources when closing the window"""
        logger.info("Application closing")
        
        # Stop any ongoing recording
        if self.is_recording and self.recording_manager:
            self.recording_manager.stop_recording()
            
        # Release audio resources
        if self.recording_manager:
            try:
                # Properly release resources
                self.recording_manager.release()
                logger.info("Released recording manager resources")
            except Exception as e:
                logger.error(f"Error releasing recording resources: {e}")
            
        # Close the window
        self.root.destroy()


# Main execution code for Tkinter application
if __name__ == "__main__":
    try:
        # Create the root window
        root = tk.Tk()
        
        # Create the application
        app = OllamaChatApp(root)
        
        # Start the main event loop
        logger.info("Starting Tkinter main loop")
        root.mainloop()
        logger.info("Tkinter main loop exited")
    except Exception as e:
        logger.critical(f"Fatal error in main thread: {e}", exc_info=True)