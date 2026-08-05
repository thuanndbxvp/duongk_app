from pydantic import BaseModel

class VoiceSynthesizeRequest(BaseModel):
    text: str
    voice_profile_id: str
