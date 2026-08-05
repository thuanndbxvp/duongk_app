import modal

def clone_voice_from_modal(text: str, reference_audio_url: str, output_key: str):
    """
    Calls the synthesize_voice function on Modal.
    Returns the public audio URL.
    """
    synth_fn = modal.Function.lookup("ai-dubbing-pipeline", "synthesize_voice")
    result = synth_fn.remote(text=text, reference_audio_url=reference_audio_url, output_key=output_key)
    return result

def clone_voice_async(text: str, reference_audio_url: str, output_key: str):
    """
    Spawns the synthesize_voice function asynchronously.
    """
    synth_fn = modal.Function.lookup("ai-dubbing-pipeline", "synthesize_voice")
    call = synth_fn.spawn(text=text, reference_audio_url=reference_audio_url, output_key=output_key)
    return call.object_id
