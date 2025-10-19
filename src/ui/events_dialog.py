import tkinter as tk
from tkinter import ttk
import queue

from models.events import events


class EventsViewModel:
    def __init__(self):
        self.display_items = []
        self.queue = queue.Queue()
        self.view = None

    def set_view(self, view):
        self.view = view

    def add_event(self, event):
        self.queue.put(event)

    def process_queue(self):
        updated = False
        while not self.queue.empty():
            event = self.queue.get()
            # Business logic: format event for display
            if isinstance(event, events.ErrorEvent):
                item = {"text": f"❌ Error: {event.message}", "tag": "error"}
            elif isinstance(event, events.SuccessEvent):
                item = {"text": f"✅ Success: {event.message}", "tag": "success"}
            else:
                item = {"text": f"ℹ️ Event: {event.message}", "tag": "normal"}
            self.display_items.append(item)
            updated = True
        if updated and self.view:
            self.view.update()


class EventsDialog:
    def __init__(self, view_model: EventsViewModel):
        self.view_model = view_model
        self.view_model.set_view(self)

        self.root = tk.Tk()
        self.root.title("Storey Allocation Events Summary")
        self.root.geometry("600x400")
        self.root.resizable(True, True)

        # modal
        self.root.grab_set()
        self.root.focus_set()

        label = ttk.Label(self.root, text="Summary of Events:")
        label.pack(pady=10)

        self.text = tk.Text(self.root, wrap=tk.WORD, height=15, state=tk.NORMAL)
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text.tag_configure("error", foreground="red")
        self.text.tag_configure("success", foreground="green")
        self.text.tag_configure("normal", foreground="black")

        # Initial update
        self.update()

        close_button = ttk.Button(self.root, text="Close", command=self.on_closing)
        close_button.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.after_id = None
        # Start polling the queue
        self.poll_queue()

    def on_closing(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.root.destroy()

    def poll_queue(self):
        self.view_model.process_queue()
        self.after_id = self.root.after(100, self.poll_queue)

    def update(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        for item in self.view_model.display_items:
            self.text.insert(tk.END, item["text"] + "\n", item["tag"])
        self.text.config(state=tk.DISABLED)
        self.text.see(tk.END)  # Scroll to the end

    def show(self):
        self.root.mainloop()
