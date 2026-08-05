# Bối cảnh (CONTEXT): Task 1.3 - Xây dựng YouTube Client & Quota Engine

Mục đích: Xây dựng core class gọi YouTube API, tự động đảo key (Key Rotation) khi dính 403 (hết quota) và dùng Exponential Backoff khi dính 500/503.