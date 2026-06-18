import pyttsx3
import threading
import queue

class VoiceSpeaker:
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.current_engine = None # Keep track of the active engine
        
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        
    def stop_speaking(self):
        """Immediately clears the queue and halts the active voice mid-sentence."""
        # 1. Wipe out any pending sentences in the queue
        with self.speech_queue.mutex:
            self.speech_queue.queue.clear()
            
        # 2. Force-stop the hardware engine if it is currently talking
        if self.current_engine:
            try:
                self.current_engine.stop()
            except Exception:
                pass

    def _process_queue(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass

        while True:
            text = self.speech_queue.get()
            if text is None:
                break
            try:
                self.current_engine = pyttsx3.init()
                self.current_engine.setProperty('rate', 145) 
                
                voices = self.current_engine.getProperty('voices')
                if len(voices) > 1:
                    self.current_engine.setProperty('voice', voices[1].id)
                    
                self.current_engine.say(text)
                self.current_engine.runAndWait()
                
            except Exception as e:
                print(f"[Speaker Error]: {e}")
            finally:
                # Always clean up the engine safely
                if self.current_engine:
                    del self.current_engine
                    self.current_engine = None
                    
            self.speech_queue.task_done()

    def speak(self, text: str):
        self.speech_queue.put(text)