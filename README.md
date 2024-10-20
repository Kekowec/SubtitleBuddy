# SubtitleBuddy

Simple video player with in-built subtitle generator. Tested only with Python 3.10.

Supported languages: Afrikaans, Albanian, Arabic, Armenian, Azerbaijani, Basque, Belarusian, Bengali,
Bosnian, Bulgarian, Catalan, Cebuano, Chinese (simplified), Chinese (traditional), Croatian, Czech, Danish, Dutch, English, Esperanto, Estonian, Filipino, Finnish, French, Galician, Georgian, German, Greek, Gujarati, Haitian creole, Hausa, Hebrew, Hindi, Hmong, Hungarian, Icelandic, Igbo, Indonesian, Irish, Italian, Japanese, Javanese, Kannada, Kazakh, Khmer, Korean, Lao, Latin, Latvian, Lithuanian, Macedonian, Malay, Maltese, Maori, Marathi, Mongolian, Nepali, Norwegian, Persian, Polish, Portuguese, Punjabi, Romanian, Serbian, Slovak, Slovenian, Somali, Spanish, Swahili, Swedish, Tamil, Telugu, Thai, Turkish, Ukrainian, Urdu, Vietnamese, Welsh, Yiddish, Yoruba, Zulu.

# Supported format:
- .mp4

# How to launch on Windows:
- Ensure you have Python installed and created virtual environment in the app directory;
- ```git clone https://github.com/kekowec/subtitlebuddy```
- ```python -m venv subtitlebuddy```
- ```cd subtitlebuddy```
- ```scripts\activate```
- ```pip install --no-cache-dir opencv-python pygame pyqt5 moviepy openai-whisper pysrt deep_translator```
- ```python app.py```
- Check "Translate" and enter language you want subtitles to be translated to;
- Press "Open Video";
- Wait for app to generate subtitles and press "Play" when you'll get message that subtitles are ready.
# How to launch on Linux:
- Ensure you have Python installed and created virtual environment in the app directory;
- ```git clone https://github.com/kekowec/subtitlebuddy```
- ```python -m venv subtitlebuddy```
- ```cd subtitlebuddy```
- ```source bin/activate```
- ```pip install opencv-python pygame pyqt5 moviepy openai-whisper pysrt deep_translator```
- ```python app.py```
- Check "Translate" and enter language you want subtitles to be translated to;
- Press "Open Video";
- Wait for app to generate subtitles and press "Play" when you'll get message that subtitles are ready.

