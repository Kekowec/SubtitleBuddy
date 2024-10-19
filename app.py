import sys
import os
import cv2
import pygame
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QFileDialog, 
                             QProgressBar, QCheckBox, QLineEdit, QCompleter)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from moviepy.editor import VideoFileClip
import whisper
import pysrt
from deep_translator import GoogleTranslator
import time
class SubtitleGenerator(QThread):
    subtitle_ready = pyqtSignal(list)
    progress_update = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    def __init__(self, video_path, translate=False, target_language=''):
        super().__init__()
        self.video_path = video_path
        self.subtitles = []
        self.translate = translate
        self.target_language = target_language
    def run(self):
        try:
            model = whisper.load_model("turbo")
            audio_file = self.video_path
            result = model.transcribe(audio_file)
            subs = pysrt.SubRipFile()
            sub_idx = 1
            total_segments = len(result["segments"])
            for i, segment in enumerate(result["segments"]):
                start_time = segment["start"]
                end_time = segment["end"]
                text = segment["text"]
                sub = pysrt.SubRipItem(index=sub_idx, 
                                       start=pysrt.SubRipTime(seconds=start_time), 
                                       end=pysrt.SubRipTime(seconds=end_time), 
                                       text=text)
                subs.append(sub)
                sub_idx += 1
                self.subtitles.append((start_time, text))
                progress = int((i + 1) / total_segments * 100)
                self.progress_update.emit(progress)
            if self.translate and self.target_language:
                translator = GoogleTranslator(source='auto', target=self.target_language)
                translated_subs = []
                for i, (time, text) in enumerate(self.subtitles):
                    translated_text = translator.translate(text)
                    translated_subs.append((time, translated_text))
                    progress = int((i + 1) / len(self.subtitles) * 100)
                    self.progress_update.emit(progress)
                self.subtitles = translated_subs
            self.subtitle_ready.emit(self.subtitles)
        except Exception as e:
            self.error_occurred.emit(str(e))

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        pygame.mixer.init()
    def initUI(self):
        self.setWindowTitle('Video Player with Audio')
        self.setGeometry(100, 100, 800, 600)
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.open_button = QPushButton('Open Video')
        self.open_button.clicked.connect(self.open_file)
        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.play_pause)
        self.play_button.setEnabled(False)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.subtitle_label = QLabel('Subtitles will appear here')
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("background-color: black; color: white;")
        control_layout.addWidget(self.open_button)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.slider)
        control_layout.addWidget(QLabel("Volume:"))
        control_layout.addWidget(self.volume_slider)
        main_layout.addWidget(self.video_label)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.subtitle_label)
        self.translate_checkbox = QCheckBox("Translate")
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("Target language")
        self.setup_language_autocomplete()
        control_layout.addWidget(self.translate_checkbox)
        control_layout.addWidget(self.language_input)
        self.setLayout(main_layout)
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.audio = None
        self.subtitle_generator = None
        self.subtitles = []
        self.current_subtitle_index = 0
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        self.start_time = 0
        self.paused_time = 0
    def setup_language_autocomplete(self):
        languages = [
            "afrikaans", "albanian", "arabic", "armenian", "azerbaijani", "basque", "belarusian", "bengali",
            "bosnian", "bulgarian", "catalan", "cebuano", "chinese (simplified)", "chinese (traditional)",
            "croatian", "czech", "danish", "dutch", "english", "esperanto", "estonian", "filipino", "finnish",
            "french", "galician", "georgian", "german", "greek", "gujarati", "haitian creole", "hausa",
            "hebrew", "hindi", "hmong", "hungarian", "icelandic", "igbo", "indonesian", "irish", "italian",
            "japanese", "javanese", "kannada", "kazakh", "khmer", "korean", "lao", "latin", "latvian",
            "lithuanian", "macedonian", "malay", "maltese", "maori", "marathi", "mongolian", "nepali",
            "norwegian", "persian", "polish", "portuguese", "punjabi", "romanian", "serbian",
            "slovak", "slovenian", "somali", "spanish", "swahili", "swedish", "tamil", "telugu", "thai",
            "turkish", "ukrainian", "urdu", "vietnamese", "welsh", "yiddish", "yoruba", "zulu"
        ]
        completer = QCompleter(languages)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.language_input.setCompleter(completer)
    def open_file(self):
        video_extensions = "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "",
            f"Video Files ({video_extensions});;All Files (*)"
        )
        if filename != '':
            self.cap = cv2.VideoCapture(filename)
            self.play_button.setEnabled(False)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.slider.setRange(0, self.total_frames)
            video = VideoFileClip(filename)
            audio_filename = os.path.splitext(filename)[0] + "_audio.mp3"
            video.audio.write_audiofile(audio_filename)
            video.close()
            pygame.mixer.music.load(audio_filename)
            self.audio = pygame.mixer.music
            self.play_button.setText('Play')
            self.is_playing = False
            self.current_frame = 0
            translate = self.translate_checkbox.isChecked()
            target_language = self.language_input.text()
            self.subtitle_generator = SubtitleGenerator(filename, translate, target_language)
            self.subtitle_generator.subtitle_ready.connect(self.set_subtitles)
            self.subtitle_generator.progress_update.connect(self.update_progress)
            self.subtitle_generator.error_occurred.connect(self.handle_error)
            self.subtitle_generator.start()
            self.subtitle_label.setText("Generating subtitles...")
            self.progress_bar.setVisible(True)
    def set_subtitles(self, subtitles):
        self.subtitles = subtitles
        self.current_subtitle_index = 0
        self.play_button.setEnabled(True)
        self.subtitle_label.setText("Subtitles ready. Press Play to start.")
        self.progress_bar.setVisible(False)
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    def handle_error(self, error_message):
        self.subtitle_label.setText(f"Error: {error_message}")
        self.progress_bar.setVisible(False)
        self.play_button.setEnabled(True)
    def update_subtitle_display(self, current_time):
        if self.subtitles:
            while self.current_subtitle_index < len(self.subtitles) and current_time >= self.subtitles[self.current_subtitle_index][0]:
                _, text = self.subtitles[self.current_subtitle_index]
                self.subtitle_label.setText(text)
                self.current_subtitle_index += 1
            if self.current_subtitle_index > 0 and current_time < self.subtitles[self.current_subtitle_index - 1][0]:
                self.subtitle_label.setText("")
                self.current_subtitle_index = 0
    def play_pause(self):
        if self.cap is None or not self.subtitles:
            return
        if self.play_button.text() == 'Restart':
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame = 0
            self.current_subtitle_index = 0
            self.start_time = time.time()
            pygame.mixer.music.play()
            self.play_button.setText('Pause')
            self.is_playing = True
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            interval = int(1000 / fps)
            self.timer.start(interval)
        elif self.is_playing:
            self.timer.stop()
            self.audio.pause()
            self.paused_time = time.time() - self.start_time
            self.play_button.setText('Play')
            self.is_playing = False
        else:
            self.start_time = time.time() - self.paused_time
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            interval = int(1000 / fps)
            self.timer.start(interval)
            if self.current_frame == 0:
                self.audio.play()
            else:
                self.audio.unpause()
            self.play_button.setText('Pause')
            self.is_playing = True

    def update_frame(self):
        if self.cap is None:
            return
        
        current_time = time.time() - self.start_time
        target_frame = int(current_time * self.cap.get(cv2.CAP_PROP_FPS))
        
        if target_frame > self.current_frame:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.video_label.setPixmap(QPixmap.fromImage(q_image))
                self.current_frame = target_frame
                self.slider.setValue(self.current_frame)
                self.update_subtitle_display(current_time)
            else:
                self.timer.stop()
                self.audio.stop()
                self.play_button.setText('Restart')
                self.is_playing = False
    def set_position(self, position):
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
            self.current_frame = position
            self.start_time = time.time() - (position / self.cap.get(cv2.CAP_PROP_FPS))
            pygame.mixer.music.play(start=position / self.cap.get(cv2.CAP_PROP_FPS))
            if not self.is_playing:
                self.audio.pause()
    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume / 100.0)
    def update_subtitle(self, text):
        self.subtitles.append((len(self.subtitles) * 5, text))
    def update_subtitle_display(self, current_time):
        if self.subtitles:
            while self.current_subtitle_index < len(self.subtitles) and current_time >= self.subtitles[self.current_subtitle_index][0]:
                _, text = self.subtitles[self.current_subtitle_index]
                self.subtitle_label.setText(text)
                self.current_subtitle_index += 1
            if self.current_subtitle_index > 0 and current_time < self.subtitles[self.current_subtitle_index - 1][0]:
                self.subtitle_label.setText("")
                self.current_subtitle_index = 0
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_O:
            self.open_file()
        elif event.key() == Qt.Key_Space:
            self.play_pause()
        elif event.key() == Qt.Key_Right:
            if self.cap is not None:
                current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                new_pos = current_pos + 150  #30fps
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
                pygame.mixer.music.play(start=new_pos / self.cap.get(cv2.CAP_PROP_FPS))
        elif event.key() == Qt.Key_Left:
            if self.cap is not None:
                current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                new_pos = max(0, current_pos - 150)  #30fps
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
                pygame.mixer.music.play(start=new_pos / self.cap.get(cv2.CAP_PROP_FPS))
    def closeEvent(self, event):
        if self.cap is not None:
            self.cap.release()
        pygame.mixer.quit()
        event.accept()
def main():
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()