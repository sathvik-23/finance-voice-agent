 with transcription result
        """
        try:
            # Handle different input types
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                if isinstance(audio_data, bytes):
                    temp_file.write(audio_data)
                    temp_file.flush()
                elif hasattr(audio_data, 'read'):
                    # It's a file-like object
                    temp_file.write(audio_data.read())
                    temp_file.flush()
                elif isinstance(audio_data, str) and audio_data.startswith("data:audio"):
                    # It's a base64 data URI
                    _, encoded = audio_data.split(",", 1)
                    temp_file.write(base64.b64decode(encoded))
                    temp_file.flush()
                else:
                    return {"success": False, "error": "Unsupported audio data format"}
                
                # Use OpenAI's Whisper API for transcription
                with open(temp_file.name, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                return {
                    "success": True,
                    "text": transcript.text,
                    "engine": "whisper"
                }
        
        except Exception as e:
            logger.error(f"Error in speech to text conversion: {e}")
            
            # Try fallback to local speech recognition
            try:
                r = sr.Recognizer()
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                    if isinstance(audio_data, bytes):
                        temp_file.write(audio_data)
                        temp_file.flush()
                    elif hasattr(audio_data, 'read'):
                        # It's a file-like object
                        temp_file.write(audio_data.read())
                        temp_file.flush()
                    elif isinstance(audio_data, str) and audio_data.startswith("data:audio"):
                        # It's a base64 data URI
                        _, encoded = audio_data.split(",", 1)
                        temp_file.write(base64.b64decode(encoded))
                        temp_file.flush()
                    else:
                        return {"success": False, "error": "Unsupported audio data format"}
                    
                    with sr.AudioFile(temp_file.name) as source:
                        audio = r.record(source)
                        text = r.recognize_google(audio)
                        
                        return {
                            "success": True,
                            "text": text,
                            "engine": "google"
                        }
            
            except Exception as fallback_error:
                logger.error(f"Fallback speech recognition also failed: {fallback_error}")
                return {"success": False, "error": f"Speech recognition failed: {str(e)}"}
    
    def text_to_speech(self, text: str, voice: str = "default") -> Dict[str, Any]:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (default, male, female)
            
        Returns:
            Dictionary with audio data
        """
        try:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                # Use OpenAI's TTS API
                response = self.client.audio.speech.create(
                    model="tts-1",
                    voice=self._map_voice_to_openai(voice),
                    input=text
                )
                
                # Save to temporary file
                response.stream_to_file(temp_file.name)
                
                # Read the file back
                with open(temp_file.name, "rb") as audio_file:
                    audio_data = audio_file.read()
                
                # Clean up
                os.unlink(temp_file.name)
                
                # Convert to base64 for web playback
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                
                return {
                    "success": True,
                    "audio_data": audio_base64,
                    "format": "mp3",
                    "engine": "openai"
                }
        
        except Exception as e:
            logger.error(f"Error in text to speech conversion: {e}")
            
            # Try fallback to local TTS
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    # Set voice properties
                    voices = self.tts_engine.getProperty('voices')
                    if voice == "male" and len(voices) > 0:
                        self.tts_engine.setProperty('voice', voices[0].id)
                    elif voice == "female" and len(voices) > 1:
                        self.tts_engine.setProperty('voice', voices[1].id)
                    
                    # Generate speech
                    self.tts_engine.save_to_file(text, temp_file.name)
                    self.tts_engine.runAndWait()
                    
                    # Read the file back
                    with open(temp_file.name, "rb") as audio_file:
                        audio_data = audio_file.read()
                    
                    # Clean up
                    os.unlink(temp_file.name)
                    
                    # Convert to base64 for web playback
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                    
                    return {
                        "success": True,
                        "audio_data": audio_base64,
                        "format": "wav",
                        "engine": "pyttsx3"
                    }
            
            except Exception as fallback_error:
                logger.error(f"Fallback TTS also failed: {fallback_error}")
                return {"success": False, "error": f"Text-to-speech failed: {str(e)}"}
    
    def _map_voice_to_openai(self, voice: str) -> str:
        """Map voice type to OpenAI voice options."""
        voice_map = {
            "default": "alloy",
            "male": "onyx",
            "female": "nova",
            "alloy": "alloy",
            "echo": "echo",
            "fable": "fable",
            "onyx": "onyx",
            "nova": "nova",
            "shimmer": "shimmer"
        }
        return voice_map.get(voice.lower(), "alloy")
    
    def process_voice_query(self, audio_data: Union[bytes, BinaryIO, str]) -> Dict[str, Any]:
        """
        Process a voice query by converting speech to text.
        
        Args:
            audio_data: Audio data
            
        Returns:
            Dictionary with query text
        """
        # Convert speech to text
        stt_result = self.speech_to_text(audio_data)
        
        if stt_result["success"]:
            return {
                "success": True,
                "query": stt_result["text"],
                "engine": stt_result["engine"]
            }
        else:
            return stt_result
    
    def generate_voice_response(self, text: str, voice: str = "default") -> Dict[str, Any]:
        """
        Generate a voice response from text.
        
        Args:
            text: Response text
            voice: Voice to use
            
        Returns:
            Dictionary with audio data
        """
        # Convert text to speech
        tts_result = self.text_to_speech(text, voice)
        
        if tts_result["success"]:
            return {
                "success": True,
                "response_text": text,
                "audio_data": tts_result["audio_data"],
                "format": tts_result["format"],
                "engine": tts_result["engine"]
            }
        else:
            return tts_result
