import modal

pipeline_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git")
    .pip_install("torch", "torchaudio", "omnivoice @ git+https://github.com/k2-fsa/OmniVoice.git@0.2.0")
)

app = modal.App("test-omnivoice-api")

@app.function(image=pipeline_image)
def test_api():
    from omnivoice.models.omnivoice import OmniVoiceGenerationConfig
    from omnivoice import OmniVoice
    import inspect
    print("OmniVoiceGenerationConfig fields:")
    import dataclasses
    if dataclasses.is_dataclass(OmniVoiceGenerationConfig):
        for f in dataclasses.fields(OmniVoiceGenerationConfig):
            print(f.name)
    else:
        print(OmniVoiceGenerationConfig().__dict__.keys())
        
    print("\nOmniVoice.generate signature:")
    print(inspect.signature(OmniVoice.generate))

@app.local_entrypoint()
def main():
    test_api.remote()
