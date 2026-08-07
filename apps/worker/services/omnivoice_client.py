import modal

def clone_voice_from_modal(text: str, reference_audio_url: str, output_key: str, engine: str = "vieneu"):
    """
    Calls the synthesize_vieneu or synthesize_voice function on Modal.
    Returns the public audio URL.
    """
    fn_name = "synthesize_vieneu" if engine == "vieneu" else "synthesize_voice"
    synth_fn = modal.Function.lookup("ai-dubbing-pipeline", fn_name)
    result = synth_fn.remote(text=text, reference_audio_url=reference_audio_url, output_key=output_key)
    return result

def clone_voice_async(text: str, reference_audio_url: str, output_key: str, engine: str = "vieneu"):
    """
    Spawns the synthesize_vieneu or synthesize_voice function asynchronously.
    """
    fn_name = "synthesize_vieneu" if engine == "vieneu" else "synthesize_voice"
    synth_fn = modal.Function.lookup("ai-dubbing-pipeline", fn_name)
    call = synth_fn.spawn(text=text, reference_audio_url=reference_audio_url, output_key=output_key)
    return call.object_id
