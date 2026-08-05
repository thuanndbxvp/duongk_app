# Phân bổ Kỹ năng (SKILL-ROUTING): Task 2.3

## 1. Chiến lược tổng thể
Task này sử dụng OpenAI GPT-4o và Vision API. Cần:
- Async OpenAI client
- Structured JSON output
- Cost tracking
- Versioning logic

## 2. Bảng Phân bổ

| Step | Task | Primary Skill | Reference |
|------|------|---------------|-----------|
| 1 | LLM Analyzer | `general-purpose` | - |
| 2 | Prompt Templates | `general-purpose` | - |
| 3 | Vision Analyzer | `general-purpose` | - |
| 4 | Versioning Migration | `databases` | - |
| 5 | Unit Tests | `tester` | - |

## 3. Special Notes
- Cần OPENAI_API_KEY
- GPT-4o vision limit: 20 images/request
- Cost cap: track token usage
