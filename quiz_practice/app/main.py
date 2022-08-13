"""App for QUIZ ON-AIR practice."""
import enum
import glob
import json
import os
import random
import sys

from typing import Callable

import tkinter as tk

from tkinter import messagebox
from tkinter import ttk

from quiz_practice.utils.utils import parse_xlsx

GENRE = {
    "stage1": "文学＆歴史",
    "stage2": "自然科学",
    "stage3": "現代社会＆地理",
    "stage4": "グルメ＆趣味",
    "stage5": "アニメ＆ゲーム",
}
G2S = {
    "文学＆歴史": "stage1",
    "自然科学": "stage2",
    "現代社会＆地理": "stage3",
    "グルメ＆趣味": "stage4",
    "アニメ＆ゲーム": "stage5",
}


EXE_DIR = os.path.dirname(sys.executable)
DATA_DIR = os.path.join(EXE_DIR, "data")
DATA_PATH = os.path.join(DATA_DIR, "data.quiz")
SAVE_DATA_LIST_PATH = os.path.join(DATA_DIR, "save_data_*.quiz")
REVIEW_DATA_PATH = os.path.join(DATA_DIR, "review_data.quiz")

WINDOW_WIDTH = 380
WINDOW_HEIGHT = 330
QUIZ_WINDOW_WIDTH = 400
QUIZ_WINDOW_HEIGHT = 300


class Mode(enum.Enum):
    """Practice mode."""

    NORMAL = "normal"
    RESTART = "restart"
    WRONG = "wrong"
    REVIEW = "review"


def set_window_center(window: tk.Tk, width: int, height: int) -> None:
    """Set window center."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    pos_x = int((screen_width / 2) - (width / 2))
    pos_y = int((screen_height / 2) - (height / 2))

    window.geometry(f"{width}x{height}+{pos_x}+{pos_y}")


class App(tk.Tk):
    """Application window class."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        tk.Tk.__init__(self, *args, **kwargs)

        # set root window
        self.title("もちうさドリル for Windows")
        set_window_center(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

        # set style
        self.style = ttk.Style()
        self.style.configure("Default.TLabelframe", fg="gray", bordercolor="black")
        self.style.configure("Choice.TButton", anchor=tk.W)
        self.style.configure("SelectedChoice.TButton", anchor=tk.W, background="blue")
        self.style.configure("WrongChoice.TButton", anchor=tk.W)
        self.style.configure("CorrectChoice.TButton", anchor=tk.W, background="red")

        # start rendering
        self.render_genre_selection()

    def render_genre_selection(self) -> None:
        """Render genre selection frame."""
        # set genre selection frame
        genre_select_frame = ttk.Labelframe(self, text="出題ジャンル選択", labelanchor="n", style="Default.TLabelframe")
        self.genre_ckb_list: list[ttk.Checkbutton] = []
        self.genre_ckb_vars: dict[str, tk.BooleanVar] = {}
        for stage, genre in GENRE.items():
            ckb_var = tk.BooleanVar()
            ckb_var.set(True)
            genre_ckb = ttk.Checkbutton(
                genre_select_frame,
                text=f"{genre}",
                variable=ckb_var,
                command=lambda: self.change_start_state(),
            )
            genre_ckb.pack(anchor=tk.W)
            self.genre_ckb_list.append(genre_ckb)
            self.genre_ckb_vars[stage] = ckb_var
        genre_select_frame.pack(side=tk.TOP)
        self.all_check_on_button = ttk.Button(
            genre_select_frame, text="全てにチェックを入れる", command=lambda: self.set_all_checkbutton_var(True)
        )
        self.all_check_on_button.pack(fill=tk.X)
        self.all_check_off_button = ttk.Button(
            genre_select_frame, text="全てのチェックを外す", command=lambda: self.set_all_checkbutton_var(False)
        )
        self.all_check_off_button.pack(fill=tk.X)

        # set mode selecting frame
        self.save_data_path = None
        mode_selecting_frame = ttk.Labelframe(self, text="モード選択", labelanchor="n", style="Default.TLabelframe")
        self.mode_var = tk.StringVar(value=Mode.NORMAL.value)
        self.practice_mode_button = ttk.Radiobutton(
            mode_selecting_frame,
            text="通常",
            value=Mode.NORMAL.value,
            variable=self.mode_var,
            command=lambda: self.generate_mode_select_side_effect(),
        )
        if len(glob.glob(SAVE_DATA_LIST_PATH)) == 0:
            wrong_mode_state = tk.DISABLED
        else:
            wrong_mode_state = tk.NORMAL
        self.wrong_mode_button = ttk.Radiobutton(
            mode_selecting_frame,
            text="間違えた問題のみ",
            value=Mode.WRONG.value,
            variable=self.mode_var,
            state=wrong_mode_state,
            command=lambda: self.generate_mode_select_side_effect(),
        )
        if len(glob.glob(REVIEW_DATA_PATH)) == 0:
            review_mode_state = tk.DISABLED
        else:
            review_mode_state = tk.NORMAL
        self.review_mode_button = ttk.Radiobutton(
            mode_selecting_frame,
            text="復習リストから",
            value=Mode.REVIEW.value,
            variable=self.mode_var,
            state=review_mode_state,
            command=lambda: self.generate_mode_select_side_effect(),
        )
        if len(glob.glob(SAVE_DATA_LIST_PATH)) == 0:
            restart_mode_state = tk.DISABLED
        else:
            restart_mode_state = tk.NORMAL
        self.restart_mode_button = ttk.Radiobutton(
            mode_selecting_frame,
            text="続きから",
            value=Mode.RESTART.value,
            variable=self.mode_var,
            state=restart_mode_state,
            command=lambda: self.generate_mode_select_side_effect(),
        )
        mode_selecting_frame.pack()
        self.practice_mode_button.pack(side=tk.LEFT, anchor=tk.W)
        self.wrong_mode_button.pack(side=tk.LEFT, anchor=tk.W)
        self.review_mode_button.pack(side=tk.LEFT, anchor=tk.W)
        self.restart_mode_button.pack(side=tk.LEFT, anchor=tk.W)

        # set other setting frame
        setting_frame = ttk.Frame(self)
        self.set_random_ckb_var = tk.BooleanVar()
        self.set_random_ckb_var.set(False)
        self.set_random_ckb = ttk.Checkbutton(
            setting_frame, text="ランダムに出題する", variable=self.set_random_ckb_var
        )
        self.default_review_ckb_var = tk.BooleanVar()
        self.default_review_ckb_var.set(False)
        self.default_review_ckb = ttk.Checkbutton(
            setting_frame, text="デフォルトで復習リストに追加する", variable=self.default_review_ckb_var
        )
        setting_frame.pack()
        self.set_random_ckb.pack(anchor=tk.W)
        self.default_review_ckb.pack(anchor=tk.W)

        # set start button frame
        start_button_frame = ttk.Frame(self)
        self.start_button = ttk.Button(start_button_frame, text="スタート！", command=lambda: self.render_quiz())
        start_button_frame.pack()
        self.start_button.pack()

        # set loading quiz frame
        loading_quiz_frame = ttk.Frame(self)
        self.loading_quiz_button = ttk.Button(loading_quiz_frame, text="問題集読込み", command=lambda: self.load_quiz())
        loading_quiz_frame.pack()
        self.loading_quiz_button.pack(pady=10)

        # check quiz data
        if not os.path.exists(DATA_PATH):
            self.start_button["state"] = tk.DISABLED
            messagebox.showinfo("初回起動", "まずは「問題集読込み」を押してください！")

    def set_all_checkbutton_var(self, value: bool) -> None:
        """Set all check button variables."""
        for genre_ckb_var in self.genre_ckb_vars.values():
            genre_ckb_var.set(value)
        self.change_start_state()

    def set_all_checkbutton_state(self, state: str) -> None:
        """Set all check button state."""
        for genre_ckb in self.genre_ckb_list:
            genre_ckb["state"] = state

    def set_default_review_var(self) -> None:
        """Set default review var."""
        pass

    def generate_mode_select_side_effect(self) -> None:
        """Generate side effect of mode selection."""
        if self.mode_var.get() == Mode.WRONG.value or self.mode_var.get() == Mode.RESTART.value:
            self.set_all_checkbutton_state(tk.DISABLED)
            self.all_check_on_button["state"] = tk.DISABLED
            self.all_check_off_button["state"] = tk.DISABLED
            self.start_button["text"] = "セーブデータ読込み"
            self.start_button["command"] = lambda: self.render_save_selection()
            self.set_all_checkbutton_var(True)
        else:
            self.set_all_checkbutton_state(tk.NORMAL)
            self.all_check_on_button["state"] = tk.NORMAL
            self.all_check_off_button["state"] = tk.NORMAL
            self.start_button["text"] = "スタート！"
            self.start_button["command"] = lambda: self.render_quiz()

    def change_start_state(self) -> None:
        """Change state of start button."""
        if not any([ckb_var.get() for ckb_var in self.genre_ckb_vars.values()]):
            self.start_button["state"] = tk.DISABLED
        else:
            self.start_button["state"] = tk.NORMAL

    def load_quiz(self) -> None:
        """Load quizzes."""
        self.loading_quiz_button["state"] = tk.DISABLED
        xlsx_path = os.path.join(EXE_DIR, "クイズオンエア問題集.xlsx")
        if os.path.exists(xlsx_path):
            parse_xlsx(xlsx_path=xlsx_path, save_path=DATA_PATH)
            messagebox.showinfo("問題集読込み", "読込み完了！")
            self.start_button["state"] = tk.NORMAL
        else:
            messagebox.showerror("問題集読込み", f"{xlsx_path} が見つかりません！\n問題集をダウンロードして同じファルダに置いてください！")
        self.loading_quiz_button["state"] = tk.NORMAL

    def render_quiz(self) -> None:
        """Render quiz window."""
        self.quiz_window = tk.Toplevel()
        self.quiz_window.title("もちうさドリル for Windows")
        set_window_center(self.quiz_window, width=QUIZ_WINDOW_WIDTH, height=QUIZ_WINDOW_HEIGHT)

        self.quiz_window.grab_set()
        self.quiz_window.focus_set()

        # count save data
        self.save_data_count = len(glob.glob(SAVE_DATA_LIST_PATH))

        # load review quizzes
        self.review_qid_info: dict[str, list[str]] = {}
        for stage in GENRE.keys():
            self.review_qid_info[stage]: list[str] = []
        if not os.path.exists(REVIEW_DATA_PATH):
            self.review_quizzes: dict[str, dict[str, list[dict[str, str | list[str]]]]] = {}
            for stage in GENRE.keys():
                self.review_quizzes[stage] = {"quiz_list": []}
        else:
            with open(REVIEW_DATA_PATH, encoding="utf-8") as f:
                self.review_quizzes = json.load(f)
            for stage in GENRE.keys():
                for quiz in self.review_quizzes[stage]["quiz_list"]:
                    self.review_qid_info[stage].append(quiz["qid"])

        match self.mode_var.get():
            case Mode.NORMAL.value:
                with open(DATA_PATH, encoding="utf-8") as f:
                    data = json.load(f)
            case Mode.WRONG.value:
                with open(self.save_data_path, encoding="utf-8") as f:
                    save_data = json.load(f)
                    data: dict[str, dict[str, list[dict[str, str | list[str]]]]] = save_data["wrong_quizzes"]
                    self.saved_restart_quizzes = save_data["restart_quizzes"]
            case Mode.REVIEW.value:
                with open(REVIEW_DATA_PATH, encoding="utf-8") as f:
                    data = json.load(f)
            case Mode.RESTART.value:
                with open(self.save_data_path, encoding="utf-8") as f:
                    save_data = json.load(f)
                    data = save_data["restart_quizzes"]
                    wrong_quizzes: dict[str, dict[str, list[dict[str, str | list[str]]]]] = save_data["wrong_quizzes"]
            case _:
                raise ValueError("Unknown mode.")

        self.quizzes: list[dict[str, str | list[str]]] = []
        self.restart_quizzes: dict[str, dict[str, list[dict[str, str | list[str]]]]] = {}
        self.wrong_quizzes: dict[str, dict[str, list[dict[str, str | list[str]]]]] = {}
        print("Check genre...")
        for stage, genre_ckb_var in self.genre_ckb_vars.items():
            if genre_ckb_var.get():
                quiz_list = data[stage]["quiz_list"]
                self.quizzes.extend(quiz_list)
            self.restart_quizzes[stage] = {"quiz_list": []}
            match self.mode_var.get():
                case Mode.NORMAL.value:
                    self.wrong_quizzes[stage] = {"quiz_list": []}
                case Mode.WRONG.value:
                    self.wrong_quizzes[stage] = {"quiz_list": []}
                case Mode.REVIEW.value:
                    self.wrong_quizzes[stage] = {"quiz_list": []}
                case Mode.RESTART.value:
                    self.wrong_quizzes[stage] = wrong_quizzes[stage]
                case _:
                    raise ValueError("Unknown mode.")
        if self.set_random_ckb_var.get():
            random.shuffle(self.quizzes)

        # set progress frame
        progress_frame = ttk.Frame(self.quiz_window)
        self.progress_label = ttk.Label(progress_frame, text="(/) ジャンル：")
        self.progress_label.pack()
        progress_frame.pack()

        # set quiz frame
        quiz_frame = ttk.Labelframe(
            self.quiz_window,
            labelanchor="n",
            text="問題",
            style="Default.TLabelframe",
            width=380,
            height=200,
        )
        self.quiz_label = ttk.Label(quiz_frame, text="ジャンルを選択してね！", wraplength="380")
        self.quiz_label.pack(anchor=tk.W)
        quiz_frame.pack()

        # set save frame
        save_frame = ttk.Frame(self.quiz_window)
        self.save_button = ttk.Button(save_frame, text="ここまでを記録して終了", command=lambda: self.pre_quiz_window_close())
        save_frame.pack(side=tk.BOTTOM)
        self.save_button.pack()

        # set margin frame
        margin_frame = ttk.Frame(self.quiz_window)
        margin_label = ttk.Label(margin_frame, text="")
        margin_frame.pack(side=tk.BOTTOM)
        margin_label.pack()

        # set next frame
        next_frame = ttk.Frame(self.quiz_window)
        self.next_button = ttk.Button(next_frame, text="次の問題へ", command=lambda: self.display_next())
        self.next_button.pack()
        next_frame.pack(side=tk.BOTTOM)

        # set review check frame
        review_frame = ttk.Frame(self.quiz_window)
        self.review_check_var = tk.BooleanVar()
        self.review_check_var.set(self.default_review_ckb_var.get())
        self.review_check_button = ttk.Checkbutton(review_frame, text="復習リストに追加する", variable=self.review_check_var)
        review_frame.pack(side=tk.BOTTOM)
        self.review_check_button.pack(anchor=tk.W)

        # set choices frame
        choice_frame = ttk.Labelframe(self.quiz_window, labelanchor="n", text="選択肢", style="Default.TLabelframe")
        self.choice_button_list: list[ttk.Button] = []
        for i in range(4):
            choice_button = ttk.Button(choice_frame, text=f"#{i+1} 選択肢", style="Choice.TButton")
            choice_button.pack(anchor=tk.W, fill=tk.X)
            self.choice_button_list.append(choice_button)
        choice_frame.pack(side=tk.BOTTOM)

        # start displaying quizzes
        self.n_quizzes = len(self.quizzes)
        if self.n_quizzes == 0:
            if self.mode_var.get() == Mode.WRONG.value:
                messagebox.showinfo("もちうさドリル for Windows", "間違えた問題がないよ！")
            elif self.mode_var.get() == Mode.REVIEW.value:
                messagebox.showinfo("もちうさドリル for Windows", "復習リストに問題がないよ！")
            elif self.mode_var.get() == Mode.RESTART.value:
                messagebox.showinfo("もちうさドリル for Windows", "全て解き終わってるよ！")
            self.quiz_window.destroy()
        else:
            self.quiz_idx = 0
            self.current_quiz = None
            self.quiz_window.protocol("WM_DELETE_WINDOW", self.pre_quiz_window_close)
            self.display_quiz()

            app.wait_window(self.quiz_window)

    def display_quiz(self) -> None:
        """Display quiz."""
        # check finish
        self.is_answered = False
        if self.quiz_idx + 1 >= self.n_quizzes:
            self.next_button["text"] = "終了！"
            self.next_button["command"] = lambda: self.pre_quiz_window_close(is_finish=True)

        self.current_quiz = self.quizzes[self.quiz_idx]
        self.progress_label["text"] = f"({self.quiz_idx+1}問目 / {self.n_quizzes}問中) ジャンル: {self.current_quiz['genre']}"
        self.quiz_label["text"] = self.current_quiz["quiz"]
        answer = self.current_quiz["answer"]

        random.shuffle(self.current_quiz["choices"])
        answer_idx = None
        for idx, choice in enumerate(self.current_quiz["choices"]):
            if answer == choice:
                answer_idx = idx
        for choice_idx, (choice, choice_button) in enumerate(
            zip(self.current_quiz["choices"], self.choice_button_list)
        ):
            choice_button["text"] = f"#{choice_idx+1} {choice}"
            choice_button["style"] = "Choice.TButton"
            choice_button["command"] = self.display_answer_callback(
                selected_idx=choice_idx, answer_idx=answer_idx, answer=answer
            )

    def display_answer_callback(self, selected_idx: int, answer_idx: int, answer: str) -> Callable[[], None]:
        """Return callback for display answer."""

        def display_answer() -> None:
            """Display answer."""
            self.quiz_label["text"] = f"正解は\t #{answer_idx+1} {answer}"
            print(selected_idx)
            for idx, choice_button in enumerate(self.choice_button_list):
                choice_button["command"] = lambda: None
                if idx == answer_idx:
                    choice_button["style"] = "CorrectChoice.TButton"
                elif idx == selected_idx:
                    choice_button["style"] = "SelectedChoice.TButton"
                else:
                    choice_button["style"] = "WrongChoice.TButton"

            if selected_idx != answer_idx:
                genre = self.current_quiz["genre"]
                self.wrong_quizzes[G2S[genre]]["quiz_list"].append(self.current_quiz)
                print("wrong quiz added.")
            self.is_answered = True
            self.quiz_idx += 1

        return display_answer

    def display_next(self) -> None:
        """Display next quiz."""
        if not self.is_answered:
            self.quiz_idx += 1
        if self.review_check_var.get():
            self.add_review()
        else:
            self.remove_review()
        self.review_check_var.set(self.default_review_ckb_var.get())
        self.display_quiz()

    def add_review(self) -> None:
        """Add a quiz to review list."""
        qid = self.current_quiz["qid"]
        genre = self.current_quiz["genre"]
        stage = G2S[genre]
        if qid not in self.review_qid_info[stage]:
            self.review_quizzes[stage]["quiz_list"].append(self.current_quiz)
            self.review_qid_info[stage].append(qid)
            print("review quiz added.")

    def remove_review(self) -> None:
        """Remove a quiz in review list."""
        qid = self.current_quiz["qid"]
        genre = self.current_quiz["genre"]
        stage = G2S[genre]
        if qid in self.review_qid_info[stage]:
            quiz_list = self.review_quizzes[stage]["quiz_list"]
            for idx, quiz in enumerate(quiz_list):
                if qid == quiz["qid"]:
                    del_idx = idx
                    break
            del self.review_quizzes[stage]["quiz_list"][del_idx]
            self.review_qid_info[stage].remove(qid)
            print("review quiz removed.")

    def pre_quiz_window_close(self, is_finish: bool = False) -> None:
        """Pre-process before closing quiz window."""
        # save quizzes
        if not is_finish or not self.is_answered:
            for restart_quiz in self.quizzes[self.quiz_idx:]:
                genre = restart_quiz["genre"]
                self.restart_quizzes[G2S[genre]]["quiz_list"].append(restart_quiz)
                if self.mode_var.get() == Mode.WRONG.value:
                    self.wrong_quizzes[G2S[genre]]["quiz_list"].append(restart_quiz)
        if self.review_check_var.get():
            self.add_review()
        else:
            self.remove_review()

        save_data_filename = f"save_data_{self.save_data_count+1:03d}_{self.mode_var.get()}.quiz"
        match self.mode_var.get():
            case Mode.NORMAL.value:
                save_data = {
                    "wrong_quizzes": self.wrong_quizzes,
                    "restart_quizzes": self.restart_quizzes,
                }
                save_data_path = os.path.join(DATA_DIR, save_data_filename)
            case Mode.WRONG.value:
                save_data = {
                    "wrong_quizzes": self.wrong_quizzes,
                    "restart_quizzes": self.saved_restart_quizzes,
                }
                save_data_path = self.save_data_path
            case Mode.REVIEW.value:
                save_data = {
                    "wrong_quizzes": self.wrong_quizzes,
                    "restart_quizzes": self.restart_quizzes,
                }
                save_data_path = os.path.join(DATA_DIR, save_data_filename)
            case Mode.RESTART.value:
                save_data = {
                    "wrong_quizzes": self.wrong_quizzes,
                    "restart_quizzes": self.restart_quizzes,
                }
                save_data_path = self.save_data_path
            case _:
                raise ValueError
        with open(save_data_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)
        self.wrong_mode_button["state"] = tk.NORMAL
        self.restart_mode_button["state"] = tk.NORMAL

        # save review quizzes
        with open(REVIEW_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self.review_quizzes, f, indent=4, ensure_ascii=False)
        self.review_mode_button["state"] = tk.NORMAL

        print("closed.")
        self.quiz_window.destroy()

    def render_save_selection(self) -> None:
        """Render quiz window."""
        self.save_selection_window = tk.Toplevel()
        self.save_selection_window.title("セーブデータ選択")
        set_window_center(self.save_selection_window, width=QUIZ_WINDOW_WIDTH, height=QUIZ_WINDOW_HEIGHT)

        self.save_selection_window.grab_set()
        self.save_selection_window.focus_set()

        # load save data path list
        self.save_data_path_list = [save_data_path for save_data_path in glob.glob(SAVE_DATA_LIST_PATH)]
        save_data_path_display_list = self.save_data_path2display()

        # set save list frame
        restart_list_frame = ttk.Frame(self.save_selection_window)
        self.save_data_path_list_var = tk.StringVar(value=save_data_path_display_list)
        self.restart_list_box = tk.Listbox(restart_list_frame, listvariable=self.save_data_path_list_var)
        restart_list_scrollbar = ttk.Scrollbar(
            restart_list_frame, orient=tk.VERTICAL, command=self.restart_list_box.yview
        )
        self.restart_list_box["yscrollcommand"] = restart_list_scrollbar.set
        self.restart_list_box.select_set(0)
        restart_list_frame.pack(padx=10, pady=10)
        self.restart_list_box.pack(side=tk.LEFT)
        restart_list_scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

        # set start button frame
        restart_start_button_frame = ttk.Frame(self.save_selection_window)
        self.restart_start_button = ttk.Button(
            restart_start_button_frame, text="スタート！", command=lambda: self.set_save_data_path()
        )
        restart_start_button_frame.pack()
        self.restart_start_button.pack()

    def set_save_data_path(self) -> None:
        """Set restart data path."""
        selected_idx = self.restart_list_box.curselection()[0]
        self.save_data_path = self.save_data_path_list[selected_idx]
        self.save_selection_window.destroy()
        self.render_quiz()

    def save_data_path2display(self) -> list[str]:
        """Convert save_data_path to display format."""
        save_data_path_display_list: list[str] = []
        for save_data_path in self.save_data_path_list:
            # split save_data_{idx}_{mode}.quiz"
            filename: str = os.path.basename(save_data_path).split(".")[0]
            _, _, idx, mode = filename.split("_")
            match mode:
                case Mode.NORMAL.value:
                    display_mode = "通常"
                case Mode.WRONG.value:
                    display_mode = "間違えた問題のみ"
                case Mode.REVIEW.value:
                    display_mode = "復習リストから"
                case _:
                    raise ValueError(f"Invalid mode {mode}")
            save_data_path_display_list.append(f"{idx} {display_mode}")
        return save_data_path_display_list


if __name__ == "__main__":
    app = App()
    app.mainloop()
