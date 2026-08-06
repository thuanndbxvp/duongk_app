import json
import os

registry_path = "D:\\appDK\\apps\\omnivoice\\voice_registry.json"

voices_to_add = {
    "ban_mai": {"type": "clone", "language": "vi", "instruct": None, "ref_audio_file": "ban_mai", "display_name": "Ban Mai", "description": "Giọng nữ truyền cảm", "tags": ["vietnamese", "female"]},
    "injoyreel": {"type": "clone", "language": "vi", "instruct": None, "ref_audio_file": "injoyreel", "display_name": "Injoyreel", "description": "Giọng Injoyreel", "tags": ["vietnamese"]},
    "lan_trinh": {"type": "clone", "language": "vi", "instruct": None, "ref_audio_file": "lan_trinh", "display_name": "Lan Trinh", "description": "Giọng nữ Lan Trinh", "tags": ["vietnamese", "female"]},
    "ngan_ha": {"type": "clone", "language": "vi", "instruct": None, "ref_audio_file": "ngan_ha", "display_name": "Ngân Hà", "description": "Giọng nữ Ngân Hà", "tags": ["vietnamese", "female"]},
    "ngoc_huyen": {"type": "clone", "language": "vi", "instruct": None, "ref_audio_file": "ngoc_huyen", "display_name": "Ngọc Huyền", "description": "Giọng nữ Ngọc Huyền", "tags": ["vietnamese", "female"]},
    "thao_trinh": {"type": "clone", "language": "vi", "instruct": None, "ref_audio_file": "thao_trinh", "display_name": "Thảo Trinh", "description": "Giọng nữ Thảo Trinh", "tags": ["vietnamese", "female"]},
    "tuong_vy": {"type": "clone", "language": "vi", "instruct": None, "ref_audio_file": "tuong_vy", "display_name": "Tường Vy", "description": "Giọng nữ Tường Vy", "tags": ["vietnamese", "female"]}
}

with open(registry_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
    
data['voices'].update(voices_to_add)

with open(registry_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    
print("Updated voice_registry.json")
