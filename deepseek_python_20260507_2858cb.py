import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os

DATA_FILE = "mydata.json"


class AutoSaveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("信息分类记录器")
        self.root.geometry("600x450")

        # 数据结构：{ 分类名称: [条目内容1, 条目内容2, ...] }
        self.data = {}

        # 分类顺序
        self.category_order = []

        # 每个分类对应的内部控件引用
        # self.tab_frames[category] = 该分类tab下的主frame
        self.tab_frames = {}
        # self.entry_widgets[category] = 该分类下所有Text控件的列表
        self.entry_widgets = {}
        # self.canvas_frames[category] = canvas内部用于放置条目的frame
        self.canvas_frames = {}

        # 主界面布局
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        add_cat_btn = tk.Button(top_frame, text="➕ 添加分类", command=self.add_category)
        add_cat_btn.pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 加载已有数据
        self.load_data()

    # ------------------ 数据加载与保存 ------------------
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                if not isinstance(self.data, dict):
                    self.data = {}
            except Exception:
                self.data = {}

        # 如果没有数据，默认创建一个示例分类
        if not self.data:
            self.data = {"示例分类": ["这是一条示例记录，可删除"]}

        # 按照 JSON 中的顺序重建分类
        self.category_order = list(self.data.keys())

        # 重建所有 tab 界面
        for cat in self.category_order:
            self._create_tab(cat)

    def save_data(self):
        # 收集每个分类的条目文本
        new_data = {}
        for cat in self.category_order:
            entries = []
            if cat in self.entry_widgets:
                for text_widget in self.entry_widgets[cat]:
                    content = text_widget.get("1.0", "end-1c")  # 去除末尾换行
                    entries.append(content)
            new_data[cat] = entries
        self.data = new_data

        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存失败: {e}")

    # ------------------ 分类管理 ------------------
    def add_category(self):
        name = simpledialog.askstring("添加分类", "请输入分类名称：", parent=self.root)
        if not name:
            return
        name = name.strip()
        if not name:
            return
        if name in self.data:
            messagebox.showwarning("重复", "分类名称已存在！")
            return

        # 更新数据结构
        self.data[name] = []
        self.category_order.append(name)

        # 创建对应 tab
        self._create_tab(name)

        # 切换到新分类
        idx = self.category_order.index(name)
        self.notebook.select(idx)
        self.save_data()

    def _create_tab(self, category):
        """为一个分类创建 Notebook 页和内部可滚动条目区域"""
        # 主 tab 框架
        tab_frame = tk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=category)
        self.tab_frames[category] = tab_frame

        # 可滚动区域
        canvas = tk.Canvas(tab_frame, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 底部按钮框架
        btn_frame = tk.Frame(tab_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        add_entry_btn = tk.Button(btn_frame, text="➕ 添加条目",
                                  command=lambda c=category: self.add_entry(c))
        add_entry_btn.pack(side=tk.LEFT, padx=5)

        # 存储引用
        self.canvas_frames[category] = scrollable_frame
        self.entry_widgets[category] = []

        # 填充该分类已有的条目
        for text in self.data.get(category, []):
            self._create_entry_widget(category, text)

    # ------------------ 条目管理 ------------------
    def add_entry(self, category):
        """在指定分类下添加一个空白条目"""
        # 更新数据
        self.data[category].append("")
        # 创建界面控件
        self._create_entry_widget(category, "")
        # 自动保存
        self.save_data()

    def _create_entry_widget(self, category, text=""):
        """在 category 对应的 canvas 内部创建一个 Text 输入块"""
        parent = self.canvas_frames[category]
        frame = tk.Frame(parent, bd=1, relief=tk.RAISED, padx=3, pady=3)
        frame.pack(fill=tk.X, padx=5, pady=3, anchor="n")

        # 条目输入框（多行文本）
        text_widget = tk.Text(frame, height=3, wrap="word", undo=True)
        text_widget.insert("1.0", text)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 删除按钮
        del_btn = tk.Button(frame, text="✕", width=2, relief=tk.GROOVE,
                            command=lambda c=category, f=frame, tw=text_widget: self.delete_entry(c, f, tw))
        del_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 绑定自动保存事件
        def on_text_change(event=None):
            # 使用 after 避免频繁保存
            if hasattr(text_widget, "_save_job"):
                self.root.after_cancel(text_widget._save_job)
            text_widget._save_job = self.root.after(500, self.save_data)

        text_widget.bind("<KeyRelease>", on_text_change)
        # 也绑定粘贴、剪切等操作后的保存
        text_widget.bind("<<Paste>>", on_text_change)
        text_widget.bind("<<Cut>>", on_text_change)

        # 存储控件引用
        self.entry_widgets[category].append(text_widget)

    def delete_entry(self, category, frame, text_widget):
        """删除一个条目"""
        # 确认删除（可选，这里直接删除）
        # 获取条目在列表中的索引
        if category in self.entry_widgets:
            try:
                idx = self.entry_widgets[category].index(text_widget)
                # 从数据结构移除
                del self.data[category][idx]
                # 移除控件
                self.entry_widgets[category].remove(text_widget)
                frame.destroy()
                # 保存
                self.save_data()
            except (ValueError, IndexError):
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoSaveApp(root)
    root.mainloop()