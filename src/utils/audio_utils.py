import wave
import io

def create_wav_header(pcm_data, sample_rate=16000, channels=1, sample_width=2):
    """
    Creates a WAV file in memory from raw PCM data.
    """
    with io.BytesIO() as wav_buffer:
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        
        return wav_buffer.getvalue()
