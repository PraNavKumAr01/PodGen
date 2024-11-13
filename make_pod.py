import json
from pydub import AudioSegment
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from deepgram.client import DeepgramClient, SpeakOptions
import os
from dotenv import load_dotenv
import random
from io import BytesIO

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["DEEPGRAM_API_KEY"] = os.environ.get("DEEPGRAM_API_KEY")

VOICES = {
    "female": ["aura-asteria-en", "aura-luna-en", "aura-stella-en"],
    "male": ["aura-orpheus-en", "aura-angus-en", "aura-arcas-en"]
}

def get_response(query, num_speakers, male_count, female_count):
    llm = ChatGroq(temperature=0.4, model_name="llama-3.1-70b-versatile")

    prompt = PromptTemplate(
        input_variables=["user_query", "num_speakers", "male_count", "female_count"],
        template="""
        Generate a podcast script based on this topic: {user_query}
        
        The podcast should have {num_speakers} speakers, with {male_count} male and {female_count} female speakers.
        
        The script should be in the following JSON format:
        {{
          "podcast": {{
            "title": "Title of the podcast",
            "speakers": [
              {{"id": "S1", "gender": "male/female"}},
              {{"id": "S2", "gender": "male/female"}},
              // ... up to the specified number of speakers
            ],
            "segments": [
              {{
                "speaker": "S1",
                "text": "Speaker's dialogue..."
              }},
              // ... more segments
            ]
          }}
        }}

        IMPORTANT RULES:
        - Make sure to alternate between the order of the speakers, they dont always have to be in the same order like S1, S2, S3
        you can alternate them to make the conversation more realistic. It is vert important to have different order of speakers in
        the conversation rather than them being in order lik s1 s2 s3, keep it alternating like s1, s2, s1, s3, s2, s3, s1 etc, this is just an example order
        - Make sure to add ... (three dots) to signify longer pauses, do this to make the flow of conversation more realistic
        - Make sure to add ... (three dots) before important things or where pauses are neccessary, you can use it plenty of times
        - Use filler words between 'um' and 'uh' to add more realistic feel of the speakers speaking. But only use 'um' and 'uh' with this exact spelling
        - Add filler words like 'um' and 'uh' regularly to keep it realistic
        - The script should have atleast 6 segments per speaker
        - Keep the script as long as you can, but not more than 10 segments per speaker

        Ensure that the script has a natural conversation flow and uses all specified speakers.
        Please start directly with the json no text before or after the json.
        """
    )

    chain = prompt | llm
    response = chain.invoke({
        "user_query": query,
        "num_speakers": num_speakers,
        "male_count": male_count,
        "female_count": female_count
    })
    
    return json.loads(response.content)

def text_to_speech(transcript, voice_code):
    try:
        deepgram = DeepgramClient()
        speak_options = {"text": transcript}

        options = SpeakOptions(
            model=voice_code,
            encoding="linear16",
            container="wav"
        )

        response = deepgram.speak.v("1").stream(speak_options, options)

        return response.stream.getvalue()

    except Exception as e:
        st.write(f"Exception: {e}")

def generate_podcast(topic, num_speakers, male_count, female_count):

    st.write("Generating script")
    script = get_response(topic, num_speakers, male_count, female_count)
    with open("script.json", "w") as file:
        json.dump(script, file, indent=3)
    st.write("Script Generation Finished")
    
    speaker_voices = {}
    male_voices = VOICES["male"].copy()
    female_voices = VOICES["female"].copy()
    random.shuffle(male_voices)
    random.shuffle(female_voices)
    
    for speaker in script['podcast']['speakers']:
        if speaker['gender'] == 'male':
            speaker_voices[speaker['id']] = male_voices.pop()
        else:
            speaker_voices[speaker['id']] = female_voices.pop()

    full_podcast = AudioSegment.silent(duration=0)

    for segment in script['podcast']['segments']:
        speaker_id = segment['speaker']
        text = segment['text']
        
        voice_code = speaker_voices[speaker_id]
        
        st.write(f"Generating audio for speaker {speaker_id}")
        audio_data = text_to_speech(text, voice_code)
        
        if isinstance(audio_data, bytes):
            audio_data = BytesIO(audio_data)
        
        try:
            audio_segment = AudioSegment.from_file(audio_data, format="wav")
        except Exception as e:
            st.write(f"Error processing segment for speaker {speaker_id}: {e}")
            continue
        
        full_podcast += audio_segment

    try:
        audio_bytes = BytesIO()
        full_podcast.export(audio_bytes, format="mp3")
        audio_bytes.seek(0)

        return audio_bytes
    except Exception as e:
        st.write(f"Error generating podcast: {e}")
