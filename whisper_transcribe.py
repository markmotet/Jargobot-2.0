import whisper
from halo import Halo

load_model_spinner = Halo(text='Loading model', spinner='line')

with load_model_spinner:
    # model = whisper.load_model("base")
    model = whisper.load_model("large-v2")

load_model_spinner.succeed('Model loaded successfully!')

def transcribe_with_whisper(audio):
    
    # # load audio and pad/trim it to fit 30 seconds
    # audio = whisper.load_audio(audio)
    # audio = whisper.pad_or_trim(audio)

    # # make log-Mel spectrogram and move to the same device as the model
    # mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # # detect the spoken language
    # _, probs = model.detect_language(mel)
    # # print(f"Detected language: {max(probs, key=probs.get)}")

    # # decode the audio
    # options = whisper.DecodingOptions()
    # result = whisper.decode(model, mel, options)

    result = model.transcribe(audio)

    return result["text"]