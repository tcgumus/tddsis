import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl
from eddie.audio import record_audio, sesi_metne_donustur
from eddie.chat import chatgpt_cevap
from eddie.tts import metni_sese_donustur
from eddie.sound_device_checker import check_microphone
from eddie.sound_device_checker import check_speaker
from eddie.audio import start_recording, stop_recording  
import os
from eddie.report import generate_pdf_report, load_data
from os.path import expanduser, join
from PyQt6.QtGui import QDesktopServices

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                        QListWidgetItem, QPushButton, QLabel, QInputDialog, 
                        QMessageBox, QSplitter, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
from eddie.chat_database import ChatDatabase
import sqlite3
from eddie.sound_isolation import sound_isolation
from PyQt6.QtWidgets import ( QStackedWidget, QComboBox, QLineEdit, QFormLayout, QDialogButtonBox)

class EddieGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.last_ai_response = None 
        
        try:
            self.chat_db = ChatDatabase()

            self.current_conversation_id = self.chat_db.create_conversation()
            
            self.init_ui()
        except Exception as e:
            print(f"GUI başlatılırken hata: {str(e)}")
            error_layout = QVBoxLayout()
            error_label = QLabel(f"Uygulama başlatılırken hata oluştu:\n{str(e)}")
            error_layout.addWidget(error_label)
            self.setLayout(error_layout)

    def init_ui(self):
        try:
            self.setWindowTitle("Sesli Asistan")
            self.setGeometry(200, 200, 500, 700)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setFocus()

            # stacked widget tanimi
            self.stack = QStackedWidget(self)

            # chat sayfasi
            chat_page = QWidget()
            chat_layout = QVBoxLayout(chat_page)

            header_layout = QHBoxLayout()
            self.title_label = QLabel("Yeni Konuşma")
            self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
            header_layout.addWidget(self.title_label)
            header_layout.addStretch(1)

            self.tts_button = QPushButton("⚙️ Seçenekler")
            self.selected_tts = "OpenAI TTS"
            self.tts_button.clicked.connect(self.choose_tts)
            header_layout.addWidget(self.tts_button)

            self.new_chat_button = QPushButton("🆕 Yeni")
            self.new_chat_button.clicked.connect(self.new_conversation)
            header_layout.addWidget(self.new_chat_button)

            self.history_button = QPushButton("📚 Geçmiş")
            self.history_button.clicked.connect(self.show_history)
            header_layout.addWidget(self.history_button)

            self.rename_chat_button = QPushButton("✏️ Yeniden Adlandır")
            self.rename_chat_button.clicked.connect(self.rename_current_chat)
            header_layout.addWidget(self.rename_chat_button)

            chat_layout.addLayout(header_layout)

            self.scroll_area = QScrollArea()
            self.scroll_content = QWidget()
            self.chat_layout = QVBoxLayout(self.scroll_content)
            self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

            self.scroll_area.setWidget(self.scroll_content)
            self.scroll_area.setWidgetResizable(True)
            chat_layout.addWidget(self.scroll_area)

            button_layout = QHBoxLayout()
            self.record_button = QPushButton("🎤 Kayıt Başlat")
            self.record_button.clicked.connect(self.toggle_recording)
            button_layout.addWidget(self.record_button)

            self.play_button = QPushButton("🔊 Cevabı Dinle")
            self.play_button.clicked.connect(self.play_response)
            button_layout.addWidget(self.play_button)

            self.report_button = QPushButton("📝 Log Raporu")
            self.report_button.clicked.connect(self.gui_report)
            button_layout.addWidget(self.report_button)

            chat_layout.addLayout(button_layout)

            self.stack.addWidget(chat_page)

            #history sayfasi
            self.history_widget = ChatHistoryDialog(self.chat_db, parent=self)

            self.history_widget.cancel_button.setText("⬅️ Geri")
            self.history_widget.cancel_button.clicked.disconnect()
            self.history_widget.cancel_button.clicked.connect(
                lambda: self.stack.setCurrentIndex(0)
            )

            self.history_widget.conversation_selected.connect(self.load_conversation)
            self.history_widget.conversation_selected.connect(
                lambda _id, _msgs: self.stack.setCurrentIndex(0)
            )

            self.stack.addWidget(self.history_widget)
            
            # secenekler sayfasi
            self.options_page = QWidget()
            opt_layout = QVBoxLayout(self.options_page)
            opt_layout.setContentsMargins(40, 40, 40, 40)
            opt_layout.setSpacing(20)
            
            form_layout = QFormLayout()
            form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
            form_layout.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            
            self.tts_combo = QComboBox()
            self.tts_combo.addItems(["ElevenLabs", "OpenAI TTS"])
            form_layout.addRow("TTS Motoru Seçimi:", self.tts_combo)
            
            opt_layout.addLayout(form_layout)
            opt_layout.addStretch()       
            
            btn_opt_layout = QHBoxLayout()
            btn_opt_layout.addStretch()
            
            save_opt_btn = QPushButton("Kaydet")
            save_opt_btn.clicked.connect(self._save_options)
            btn_opt_layout.addWidget(save_opt_btn)
            
            back_opt_btn = QPushButton("⬅️ Geri")
            back_opt_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
            btn_opt_layout.addWidget(back_opt_btn)
            
            opt_layout.addLayout(btn_opt_layout)
            
            self.stack.addWidget(self.options_page)
            
            # 5) yeniden adlandir sayfasi
            self.rename_page = QWidget()
            ren_layout = QVBoxLayout(self.rename_page)
            ren_layout.setContentsMargins(40, 40, 40, 40)
            
          
            self.rename_edit = QLineEdit()
            self.rename_edit.setMaximumWidth(300)
            form_ren = QFormLayout()
            form_ren.addRow("Yeni Başlık:", self.rename_edit)
            ren_layout.addLayout(form_ren)
            ren_layout.setAlignment(form_ren, Qt.AlignmentFlag.AlignHCenter)
            
            
            buttons_ren = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok |
                QDialogButtonBox.StandardButton.Cancel
            )
            buttons_ren.button(QDialogButtonBox.StandardButton.Ok).setText("Kaydet")
            buttons_ren.button(QDialogButtonBox.StandardButton.Cancel).setText("⬅️ Geri")
            buttons_ren.accepted.connect(self._save_rename)
            buttons_ren.rejected.connect(self._back_to_main)
            btn_hbox = QHBoxLayout()
            btn_hbox.addStretch()
            btn_hbox.addWidget(buttons_ren)
            ren_layout.addLayout(btn_hbox)
            
            self.stack.addWidget(self.rename_page)

            
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(self.stack)
            self.setLayout(main_layout)

          
            self.stack.setCurrentIndex(0)
            self.add_message(
                "👋 Merhaba! Size nasıl yardımcı olabilirim?",
                is_user="Eddie",
                save_to_db=True
            )
        except Exception as e:
            print(f"GUI arayüzü oluşturulurken hata: {e}")
            QMessageBox.critical(
                self, "Hata",
                f"Uygulama arayüzü oluşturulurken hata oluştu:\n{e}"
            )

    def toggle_recording(self):
        if not self.is_recording:
            if not check_microphone():
                self.add_message("🎙 Mikrofon bulunamadı!", is_user="System", save_to_db=True)  
                return
            self.add_message("🎤 Kayıt başlatılıyor...", is_user="System", save_to_db=True)  
            start_recording()
            self.is_recording = True
            self.record_button.setText("⏹️ Kaydı Durdur")
        else:
            self.add_message("🛑 Kayıt durduruluyor...", is_user="System", save_to_db=True)  
            self.stop_and_process()
            self.is_recording = False
            self.record_button.setText("🎤 Kayıt Başlat")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.toggle_recording()

    def stop_and_process(self):
        stop_recording("voice.wav")
        if not os.path.exists("voice.wav") or os.path.getsize("voice.wav") == 0:
            self.add_message("⚠️ Kayıt alınamadı!", is_user="System", save_to_db=True)  
            return
        self.add_message("📤 Kayıt gönderiliyor, analiz ediliyor...", is_user="System", save_to_db=True)  
        self.worker = EddieWorker()
        self.worker.result_signal.connect(self.display_response)
        self.worker.start()

    def display_response(self, user_text, ai_response):
        self.add_message(user_text, is_user="User", save_to_db=True)
        self.add_message(ai_response, is_user="Eddie", save_to_db=True)
        self.last_ai_response = ai_response
        
    def play_response(self):
        if not check_speaker():
            self.add_message("🔊 Hoparlör bulunamadı!", is_user="System", save_to_db=True)
            return
        if not self.last_ai_response:
            self.add_message(
                "🔊 Seslendirilecek AI cevabı bulunamadı!",
                is_user="System", save_to_db=True
            )
            return
        metni_sese_donustur(self.last_ai_response, self.selected_tts)

    def gui_report(self):
        log_dir = join(expanduser("~"), "EddieApp", "logs")
        log_path = join(log_dir, "system_log.jsonl")
        data = load_data(log_path)
        generate_pdf_report(data)
        pdf_path = join(expanduser("~"), "EddieApp", "reports", "report.pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))

    def add_message(self, text, is_user, save_to_db=False):
        try:
            if text is None:
                text = ""
            container = QWidget()
            hl = QHBoxLayout(container)
            hl.setContentsMargins(0, 0, 0, 0)

            bubble = ChatBubble(text, is_user)
            hl.addWidget(bubble)
            self.chat_layout.addWidget(container)

            sb = self.scroll_area.verticalScrollBar()
            sb.setValue(sb.maximum())

            if save_to_db and self.current_conversation_id:
                self.chat_db.add_message(self.current_conversation_id, is_user, text)
        except Exception as e:
            print(f"Mesaj eklenirken hata: {e}")
            
    def show_history(self):
        
        self.history_widget.load_conversations()
        self.stack.setCurrentWidget(self.history_widget)
    
    def load_conversation(self, conversation_id, messages):

        try:
          
            self.clear_chat()
            self.current_conversation_id = conversation_id
 
            try:
                conn = sqlite3.connect(self.chat_db.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,))
                result = cursor.fetchone()
                title = result[0] if result else "Yüklenen Konuşma"
                conn.close()
            except Exception as e:
                print(f"Başlık yüklenirken hata: {str(e)}")
                title = "Yüklenen Konuşma"
            
            self.title_label.setText(title)

            self.last_ai_response = None  
            for sender, message in messages:
                if message: 
                    self.add_message(message, is_user=sender, save_to_db=False)
                    if sender == "Eddie":
                        self.last_ai_response = message
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Konuşma yüklenirken hata oluştu: {str(e)}")

    def clear_chat(self):
        try:
            while self.chat_layout.count():
                item = self.chat_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
        except Exception as e:
            print(f"Sohbet temizlenirken hata: {e}")
            
    def rename_current_chat(self):
        self.rename_edit.setText(self.title_label.text())
        self.stack.setCurrentWidget(self.rename_page)
    
    def new_conversation(self):
        """Yeni bir konuşma başlat"""
        try:

            self.clear_chat()

            self.current_conversation_id = self.chat_db.create_conversation()

            self.title_label.setText("Yeni Konuşma")

            self.last_ai_response = None

            self.add_message("👋 Merhaba! Size nasıl yardımcı olabilirim?", is_user="Eddie", save_to_db=True)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yeni konuşma oluşturulurken hata: {str(e)}")

    def choose_tts(self):
        idx = self.tts_combo.findText(self.selected_tts)
        if idx >= 0:
            self.tts_combo.setCurrentIndex(idx)
        self.stack.setCurrentWidget(self.options_page)
           
    def _save_options(self):
        """Options sayfasındaki seçimi kaydet ve ana sayfaya dön."""  
        self.selected_tts = self.tts_combo.currentText()
        self.stack.setCurrentIndex(0)
      
    def _save_rename(self):
        """Rename sayfasındaki başlığı kaydet ve ana sohbete dön."""
        new_title = self.rename_edit.text().strip()
        if new_title:
            self.chat_db.update_conversation_title(self.current_conversation_id, new_title)
            self.title_label.setText(new_title)
        self.stack.setCurrentIndex(0)
      
    def _back_to_main(self):
        """Geri tuşu: ana chat’e dön ve pencereyi ayarla."""
        self.stack.setCurrentIndex(0)
     
class ChatBubble(QWidget):  
    def __init__(self, text, is_user="User"):  
        super().__init__()  
        self.is_user_type = is_user
        self.init_ui(text)
        
    def init_ui(self, text):
  
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
     
        self.avatar = QLabel()
        self.avatar.setFixedSize(30, 30)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
 
        self.message = QLabel(text)  
        self.message.setWordWrap(True)  
        self.message.setStyleSheet(self.get_message_style())
        self.message.setMargin(10)

        if self.is_user_type == "User":
            layout.addStretch(1)
            layout.addWidget(self.message)
            layout.addWidget(self.avatar)
            self.avatar.setText("👤")
            self.message.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        elif self.is_user_type == "Eddie":
            layout.addWidget(self.avatar)
            layout.addWidget(self.message)
            layout.addStretch(1)
            self.avatar.setText("🤖")
            self.message.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        else: 
            layout.addStretch(1)
            layout.addWidget(self.message)
            layout.addStretch(1)
            self.message.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.avatar.setStyleSheet(self.get_avatar_style())
        
    def get_message_style(self):  
        if self.is_user_type == "User":  
            return """  
            QLabel {  
                background-color: #DCF8C6;  
                border-radius: 10px;  
                padding: 8px;  
                margin: 5px;  
                max-width: 280px;  
                color: black;  
                font-size: 14px;  
            }  
            """  
        elif self.is_user_type == "Eddie":  
            return """  
            QLabel {  
                background-color: #FFFFFF;  
                border-radius: 10px;  
                padding: 8px;  
                margin: 5px;  
                max-width: 280px;  
                color: black;  
                font-size: 14px;  
            }  
            """ 
        else:  
            return """  
            QLabel {  
                background-color: #E0E0E0;  
                border-radius: 8px;  
                padding: 6px 10px;  
                margin: 8px auto;  
                color: #333333;  
                font-size: 13px;  
                max-width: 400px;  
                text-align: center;  
            }  
            """
            
    def get_avatar_style(self):
        return """
        QLabel {
            font-size: 18px;
            border-radius: 15px;
            background-color: #f0f0f0;
            padding: 2px;
        }
        """

class ChatHistoryDialog(QDialog):
    
    conversation_selected = pyqtSignal(int, list)  # (conversation_id, message_list)

    def __init__(self, chat_db, parent=None):
        super().__init__(parent)
        self.chat_db = chat_db
        self.selected_conversation_id = None
        self.init_ui()
        self.load_conversations()

    def init_ui(self):
        self.setWindowTitle("Sohbet Geçmişi")
        if self.parent() is None:
            self.setMinimumSize(800, 500)
        else:
            self.setMinimumSize(0, 0)
 
        main_page = QWidget()
        main_layout = QVBoxLayout(main_page)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.conversation_label = QLabel("Konuşmalarım")
        self.conversation_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        left_layout.addWidget(self.conversation_label)

        self.conversation_list = QListWidget()
        self.conversation_list.setAlternatingRowColors(True)
        self.conversation_list.itemClicked.connect(self.on_conversation_selected)
        left_layout.addWidget(self.conversation_list)

        btns = QHBoxLayout()
        self.delete_button = QPushButton("Sil")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btns.addWidget(self.delete_button)

        self.rename_button = QPushButton("Yeniden Adlandır")
        self.rename_button.setEnabled(False)
        self.rename_button.clicked.connect(self.rename_conversation)
        btns.addWidget(self.rename_button)

        left_layout.addLayout(btns)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.preview_label = QLabel("Mesaj Önizleme")
        self.preview_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        right_layout.addWidget(self.preview_label)

        self.message_preview = QListWidget()
        self.message_preview.setAlternatingRowColors(True)
        self.message_preview.setWordWrap(True)
        right_layout.addWidget(self.message_preview)

        self.load_button = QPushButton("Bu Konuşmayı Yükle")
        self.load_button.setEnabled(False)
        self.load_button.clicked.connect(self.load_selected_conversation)
        right_layout.addWidget(self.load_button)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        main_layout.addWidget(splitter)

        bottom = QHBoxLayout()
        self.cancel_button = QPushButton("İptal")
        self.cancel_button.clicked.connect(self.reject)
        bottom.addWidget(self.cancel_button)
        main_layout.addLayout(bottom)

        confirm_page = QWidget()
        c_layout = QVBoxLayout(confirm_page)
        c_layout.setContentsMargins(40, 40, 40, 40)
        c_layout.setSpacing(20)

        warn_label = QLabel("Bu konuşmayı silmek istediğinizden emin misiniz?")
        warn_label.setWordWrap(True)
        c_layout.addWidget(warn_label)

        btn_hbox = QHBoxLayout()
        btn_hbox.addStretch(1)
        self.confirm_yes = QPushButton("Evet")
        self.confirm_no  = QPushButton("Hayır")
        btn_hbox.addWidget(self.confirm_yes)
        btn_hbox.addWidget(self.confirm_no)
        c_layout.addLayout(btn_hbox)
        
        self.confirm_yes.clicked.connect(self.delete_conversation)
        self.confirm_no.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        # ↓ Yeni: yeniden adlandırma sayfası 
        rename_page = QWidget()
        rp_layout = QVBoxLayout(rename_page)
        rp_layout.setContentsMargins(40, 40, 40, 40)
        rp_layout.setSpacing(20)
        
     
        self.rename_lineedit = QLineEdit()
        self.rename_lineedit.setMaximumWidth(300)
        form_layout = QFormLayout()
        form_layout.addRow("Yeni Başlık:", self.rename_lineedit)
        rp_layout.addLayout(form_layout)
    
        rp_layout.setAlignment(form_layout, Qt.AlignmentFlag.AlignHCenter)
  
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            parent=rename_page
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Kaydet")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("⬅️ Geri")
        buttons.accepted.connect(self._apply_rename)
        buttons.rejected.connect(lambda: self.stack.setCurrentIndex(0))
    
        btn_hbox = QHBoxLayout()
        btn_hbox.addStretch(1)
        btn_hbox.addWidget(buttons)
        rp_layout.addLayout(btn_hbox)
      
        self.stack = QStackedWidget(self)
        self.stack.addWidget(main_page)     # index 0
        self.stack.addWidget(confirm_page)  # index 1
        self.stack.addWidget(rename_page)   # index 2

        outer = QVBoxLayout(self)
        outer.addWidget(self.stack)   

    def load_conversations(self):
        """Veritabanından tüm konuşmaları yükle"""
        self.conversation_list.clear()
        convs = self.chat_db.get_all_conversations()
        for conv_id, title, _created, updated_at in convs:
            updated_time = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S")
            display = f"{title}\n{updated_time.strftime('%d.%m.%Y %H:%M')}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, conv_id)
            self.conversation_list.addItem(item)
     
        self.conversation_list.clearSelection()
        self.selected_conversation_id = None
        self.delete_button.setEnabled(False)
        self.rename_button.setEnabled(False)
        self.load_button.setEnabled(False)

    def on_conversation_selected(self, item):
        self.selected_conversation_id = item.data(Qt.ItemDataRole.UserRole)
        self.delete_button.setEnabled(True)
        self.rename_button.setEnabled(True)
        self.load_button.setEnabled(True)

        self.message_preview.clear()
        msgs = self.chat_db.get_conversation_messages(self.selected_conversation_id)
        for _id, sender, msg, _ts in msgs:
            prefix = "👤 Ben:" if sender == "User" else "🤖 Eddie:" if sender == "Eddie" else "🔔 Sistem:"
            preview = msg[:100] + ("..." if len(msg) > 100 else "")
            li = QListWidgetItem(f"{prefix} {preview}")
            if sender == "User":
                li.setBackground(Qt.GlobalColor.lightGray)
            self.message_preview.addItem(li)
            
    def delete_conversation(self):
        self.chat_db.delete_conversation(self.selected_conversation_id)
        self.load_conversations()
        self.message_preview.clear()
        self.selected_conversation_id = None
        self.delete_button.setEnabled(False)
        self.rename_button.setEnabled(False)
        self.load_button.setEnabled(False)
        # Ana sayfaya dön
        self.stack.setCurrentIndex(0)
        
    def rename_conversation(self):
        if self.selected_conversation_id == None:
            return
        
        current = self.conversation_list.currentItem().text().split('\n')[0]
        self.rename_lineedit.setText(current)
        
        self.stack.setCurrentIndex(2)
        
    def _apply_rename(self):
        new_title = self.rename_lineedit.text().strip()
        if new_title:
            
            self.chat_db.update_conversation_title(self.selected_conversation_id, new_title)
            
            self.load_conversations()
        
        self.stack.setCurrentIndex(0)
    
    def load_selected_conversation(self):
        if self.selected_conversation_id == None:
            return
        msgs = self.chat_db.get_conversation_messages(self.selected_conversation_id)
        msg_list = [(sender, m) for _id, sender, m, _ts in msgs]
        self.conversation_selected.emit(self.selected_conversation_id, msg_list)
        self.accept()

class EddieWorker(QThread):
    result_signal = pyqtSignal(str, str)
    
    def run(self):
        try:
            filename = "voice.wav"
            sound_isolation()
            user_text = sesi_metne_donustur("clean.wav")
            if not user_text or user_text.strip() == "":
                self.result_signal.emit("❌ Ses tanınamadı", "Whisper API yanıt vermedi veya boş döndü.")
                return
            reply = chatgpt_cevap(user_text)
            self.result_signal.emit(user_text, reply)
        except Exception as e:
            self.result_signal.emit("❌ Hata", f"{str(e)}")

        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EddieGUI()
    window.show()
    sys.exit(app.exec())