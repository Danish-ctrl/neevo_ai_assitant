import speech_recognition as sr

class VoiceListener:
    def __init__(self, wake_word="agent"):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.wake_word = wake_word.lower()
        
        with self.microphone as source:
            print("[System]: Initializing microphone and filtering background noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
            self.recognizer.dynamic_energy_threshold = True

    def listen_continuously(self) -> str:
        """Listens invisibly in the background for the wake word."""
        with self.microphone as source:
            try:
                # No more print statements here! It runs silently.
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8)
                text = self.recognizer.recognize_google(audio).lower()
                
                if self.wake_word in text:
                    parts = text.split(self.wake_word, 1)
                    command = parts[1].strip()
                    
                    if command:
                        return command
                    else:
                        # Only prints if it heard the wake word but no command
                        print("🔊 [System]: Wake word detected. Awaiting command...")
                        audio_command = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        return self.recognizer.recognize_google(audio_command).lower()
            except sr.UnknownValueError:
                pass
            except Exception:
                pass
        return ""

    def listen_active(self, timeout_seconds=8) -> str:
        """Listens directly for an answer (e.g., 'Yes') without needing the wake word."""
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(source, timeout=timeout_seconds, phrase_time_limit=10)
                return self.recognizer.recognize_google(audio).lower()
            except Exception:
                # Silently fail and go back to background listening if the user doesn't answer
                return ""