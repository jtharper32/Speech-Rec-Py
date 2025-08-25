import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import requests
import threading
import speech_recognition as sr

THINGIVERSE_APP_TOKEN = ""

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Voice Search 3D Models")
        self.geometry("700x600")
        self.configure(bg="#2e2e2e") 

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 12, 'bold'), foreground='white', background='#007acc')
        style.map('TButton', background=[('active', '#005f99')])
        style.configure('TLabel', background="#2e2e2e", foreground='white', font=('Helvetica', 11))

        self.search_button = ttk.Button(self, text="🎤 Speak to Search", command=self.start_search_thread)
        self.search_button.pack(pady=15)

        self.results_frame = ttk.Frame(self, relief=tk.RAISED)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar and canvas setup
        self.canvas = tk.Canvas(self.results_frame, bg="#1e1e1e", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style='TFrame')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Show More button
        self.show_more_button = ttk.Button(self, text="Show More Results", command=self.show_more_results)
        self.show_more_button.pack(pady=5)
        self.show_more_button.pack_forget()  # hide initially

        self.all_results = []
        self.current_index = 0
        self.results_per_page = 5

    def start_search_thread(self):
        threading.Thread(target=self.voice_search, daemon=True).start()

    def voice_search(self):
        self.clear_results()
        self.search_button.config(state=tk.DISABLED, text="Listening...")
        self.show_more_button.pack_forget()
        query = self.listen_and_recognize()
        if not query:
            self.search_button.config(state=tk.NORMAL, text="🎤 Speak to Search")
            return
        self.search_button.config(text=f"Searching: {query}")
        results = self.search_thingiverse(query)
        self.all_results = results
        self.current_index = 0
        if results:
            self.show_results(results[:self.results_per_page])
            if len(results) > self.results_per_page:
                self.show_more_button.pack(pady=5)
        else:
            self.show_message("No results found.")
        self.search_button.config(state=tk.NORMAL, text="🎤 Speak to Search")

    def listen_and_recognize(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print("You said:", text)
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            self.show_message("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Speech Recognition error: {e}")
            self.show_message("Speech Recognition service error.")
        return None

    def search_thingiverse(self, query):
        url = f"https://api.thingiverse.com/search/{query}?access_token={THINGIVERSE_APP_TOKEN}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Thingiverse API error: {response.status_code}")
            self.show_message(f"API error: {response.status_code}")
            return []
        data = response.json()
        return data.get('hits', [])

    def show_results(self, results):
        for item in results:
            frame = ttk.Frame(self.scrollable_frame, padding=10, style='TFrame')
            frame.pack(fill="x", pady=5)

            thumb_url = item.get('thumbnail')
            if thumb_url:
                try:
                    resp = requests.get(thumb_url)
                    img_data = resp.content
                    pil_image = Image.open(io.BytesIO(img_data))
                    pil_image = pil_image.resize((100, 100))
                    img = ImageTk.PhotoImage(pil_image)
                    img_label = ttk.Label(frame, image=img, background="#2e2e2e")
                    img_label.image = img  # keep ref
                    img_label.pack(side="left")
                except Exception as e:
                    print("Image load error:", e)

            name = item.get('name', 'No Name')
            url = item.get('public_url', 'No URL')
            text = f"{name}\n{url}"
            label = ttk.Label(frame, text=text, justify="left", cursor="hand2", foreground="#1e90ff", background="#2e2e2e", font=('Helvetica', 12, 'underline'))
            label.pack(side="left", padx=15)
            label.bind("<Button-1>", lambda e, url=url: self.open_url(url))

    def show_more_results(self):
        next_index = self.current_index + self.results_per_page
        results_to_show = self.all_results[self.current_index:next_index]
        self.show_results(results_to_show)
        self.current_index = next_index
        if self.current_index >= len(self.all_results):
            self.show_more_button.pack_forget()

    def open_url(self, url):
        import webbrowser
        webbrowser.open_new(url)

    def clear_results(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.current_index = 0

    def show_message(self, msg):
        self.clear_results()
        label = ttk.Label(self.scrollable_frame, text=msg, font=('Helvetica', 14), foreground='white', background="#2e2e2e")
        label.pack(pady=20)


if __name__ == "__main__":
    app = App()
    app.mainloop()

