import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.scrolledtext as st

from catalogue_app.ui.tabs.base_tab import BaseTab
from catalogue_app.agents import (
    BaseAgent,
    AnalystAgent,
    DuplicateAgent,
    SearchAgent,
    ProjectAgent,
    RenamerAgent,
    TagAgent,
)
from catalogue_app.ai_chat import chat_with_llm
from catalogue_app.db import connect as ai_connect


class ChatTab(BaseTab):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

    def _build_ui(self):
        f = self

        self.chat_history = []

        self.txt_chat = st.ScrolledText(f, wrap="word", state="disabled")
        self.txt_chat.pack(fill="both", expand=True, padx=10, pady=10)

        bot_frame = ttk.Frame(f)
        bot_frame.pack(fill="x", padx=10, pady=10)

        self.var_chat_msg = tk.StringVar()
        self.entry_chat = ttk.Entry(bot_frame, textvariable=self.var_chat_msg)
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_chat.bind("<Return>", lambda _e: self._send_chat_msg())

        self.btn_send = ttk.Button(bot_frame, text="Envoyer", command=self._send_chat_msg)
        self.btn_send.pack(side="left", padx=5)

        self._append_chat(
            "Assistant IA",
            "Bonjour ! Je suis l'assistant intelligent de Repertoir. "
            "Posez-moi une question sur vos fichiers ou votre catalogue.",
        )

    def refresh(self):
        pass

    def _set_busy(self, busy: bool):
        if busy:
            self.entry_chat.config(state="disabled")
            self.btn_send.config(state="disabled")
        else:
            self.entry_chat.config(state="normal")
            self.btn_send.config(state="normal")
            self.entry_chat.focus_set()

    def _append_chat(self, sender, text):
        self.txt_chat.config(state="normal")
        self.txt_chat.insert("end", f"{sender} : {text}\n\n")
        self.txt_chat.see("end")
        self.txt_chat.config(state="disabled")

    def _start_stream(self, sender):
        self.txt_chat.config(state="normal")
        self.txt_chat.insert("end", f"{sender} : ")
        self.txt_chat.see("end")
        self.txt_chat.config(state="disabled")

    def _append_stream(self, token):
        self.txt_chat.config(state="normal")
        self.txt_chat.insert("end", token)
        self.txt_chat.see("end")
        self.txt_chat.config(state="disabled")

    def _end_stream(self):
        self.txt_chat.config(state="normal")
        self.txt_chat.insert("end", "\n\n")
        self.txt_chat.see("end")
        self.txt_chat.config(state="disabled")

    def _send_chat_msg(self):
        msg = self.var_chat_msg.get().strip()
        if not msg:
            return
        self.var_chat_msg.set("")
        self._append_chat("Vous", msg)
        self.chat_history.append({"role": "user", "content": msg})
        self._set_busy(True)

        def stream_cb(token):
            self.after(0, lambda: self._append_stream(token))

        def worker():
            try:
                # We do NOT stream the first call because it might be an SQL query
                response = chat_with_llm(self.chat_history)

                # Check for SQL command
                if response.startswith("SQL: "):
                    sql = response[5:].strip()
                    # Pentest check: read-only queries
                    if sql.upper().startswith("SELECT"):
                        scon = None
                        try:
                            scon = ai_connect()
                            rows = scon.execute(sql).fetchall()
                            res_str = "\n".join([str(tuple(r)) for r in rows[:10]])
                            if not res_str:
                                res_str = "Aucun résultat."
                            self.chat_history.append({"role": "system", "content": f"Voici les résultats de {sql} :\n{res_str}"})

                            self.after(0, lambda: self._start_stream("Assistant IA"))
                            final_resp = chat_with_llm(self.chat_history, stream_callback=stream_cb)
                            self.after(0, lambda: self._end_stream())

                            self.chat_history.append({"role": "assistant", "content": final_resp})
                        except Exception as e:
                            self.chat_history.append({"role": "system", "content": f"Erreur SQL : {e}"})

                            self.after(0, lambda: self._start_stream("Assistant IA"))
                            final_resp = chat_with_llm(self.chat_history, stream_callback=stream_cb)
                            self.after(0, lambda: self._end_stream())

                            self.chat_history.append({"role": "assistant", "content": final_resp})
                        finally:
                            if scon is not None:
                                try:
                                    scon.close()
                                except Exception:
                                    pass
                    else:
                        err = "L'IA a tenté une action non autorisée (modification de la base de données)."
                        self.chat_history.append({"role": "assistant", "content": err})
                        self.after(0, lambda: self._append_chat("Système", err))
                else:
                    self.chat_history.append({"role": "assistant", "content": response})
                    self.after(0, lambda: self._append_chat("Assistant IA", response))
            except Exception as e:
                err_msg = f"Erreur inattendue : {e}"
                self.chat_history.append({"role": "assistant", "content": err_msg})
                self.after(0, lambda: self._append_chat("Système", err_msg))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=worker, daemon=True).start()
