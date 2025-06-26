# eddie
a shipboard computer

<img src="https://github.com/user-attachments/assets/6094f3d4-e878-43a2-935c-5812edb00f7b" width="50%">

# Kurulum
OpenAI GPT-4 + Whisper + ElevenLabs destekli sesli asistan.

```python
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

`python -m eddie.main` ile çalıştır

`pyinstaller --onefile --windowed --name Eddie eddie\gui.py` ile exe oluştur.
