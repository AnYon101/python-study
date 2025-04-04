import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from ttkbootstrap import Style
from ebooklib import epub
from bs4 import BeautifulSoup
import textwrap
import warnings

# 忽略警告
warnings.filterwarnings("ignore")

class ModernEPubReader:
    def __init__(self, root):
        self.root = root
        self.style = Style(theme='litera')  # 可选主题：cosmo, litera, minty等
        self.root.title("Modern EPUB Reader")
        self.root.geometry("2800x1600")
        
        # 初始化变量
        self.book = None
        self.chapters = []
        self.current_chapter = 0
        self.current_page = 0
        self.bookmarks = {}
        self.search_results = []
        
        # 创建UI
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="打开", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="目录", command=self.show_toc).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="书签", command=self.manage_bookmarks).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="搜索", command=self.show_search).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="设置", command=self.show_settings).pack(side=tk.LEFT, padx=2)
        
        # 搜索框（默认隐藏）
        self.search_frame = ttk.Frame(self.root)
        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(self.search_frame, text="搜索", command=self.do_search).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.search_frame, text="取消", command=self.hide_search).pack(side=tk.LEFT, padx=2)
        
        # 主内容区域
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 文本显示区域（带滚动条）
        self.text_area = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=('Microsoft YaHei', 30),
            padx=10,
            pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.config(state=tk.DISABLED)
        
        # 底部状态栏
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.chapter_label = ttk.Label(status_bar, text="章节: 0/0")
        self.chapter_label.pack(side=tk.LEFT)
        
        self.page_label = ttk.Label(status_bar, text="页码: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=20)
        
        # 导航按钮
        nav_frame = ttk.Frame(status_bar)
        nav_frame.pack(side=tk.RIGHT)
        
        ttk.Button(nav_frame, text="上一页", command=self.prev_page).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="下一页", command=self.next_page).pack(side=tk.LEFT, padx=2)
        
        # 设置默认值
        self.hide_search()
          # 应用字体抗锯齿设置（仅Windows）
        if os.name == 'nt':
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
        
    def open_file(self):
        """打开EPUB文件"""
        file_path = filedialog.askopenfilename(
            title="选择EPUB文件",
            filetypes=[("EPUB文件", "*.epub"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                self.load_epub(file_path)
                self.display_chapter()
            except Exception as e:
                messagebox.showerror("错误", f"无法加载文件:\n{str(e)}")
    
    def load_epub(self, epub_path):
        """加载并解析EPUB文件"""
        self.book = epub.read_epub(epub_path)
        self.chapters = []
        
        # 提取章节内容
        for item in self.book.get_items():
            if isinstance(item, epub.EpubHtml):
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                # 清理不需要的元素
                for elem in soup(['script', 'style', 'nav']):
                    elem.decompose()
                
                # 提取文本
                text = []
                for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'div']):
                    content = tag.get_text().strip()
                    if content:
                        if tag.name in ['h1', 'h2', 'h3']:
                            text.append(f"\n【{content}】\n")
                        else:
                            text.append(content)
                
                chapter_text = '\n'.join(text)
                if chapter_text.strip():
                    self.chapters.append(chapter_text)
        
        self.current_chapter = 0
        self.current_page = 0
        self.update_status()
    
    def display_chapter(self):
        """显示当前章节"""
        if not self.chapters:
            return
            
        # 计算分页
        chapter_text = self.chapters[self.current_chapter]
        lines = chapter_text.split('\n')
        lines_per_page = 50  # 每页行数
        
        total_pages = (len(lines) // lines_per_page) + 1
        start = self.current_page * lines_per_page
        end = start + lines_per_page
        
        # 显示文本
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, '\n'.join(lines[start:end]))
        self.text_area.config(state=tk.DISABLED)
        
        self.update_status()
    
    def update_status(self):
        """更新状态栏"""
        total_chapters = len(self.chapters) if self.chapters else 0
        total_pages = (len(self.chapters[self.current_chapter].split('\n')) // 50) + 1 if self.chapters else 0
        
        self.chapter_label.config(text=f"章节: {self.current_chapter+1}/{total_chapters}")
        self.page_label.config(text=f"页码: {self.current_page+1}/{total_pages}")
    
    def next_page(self):
        """下一页"""
        if not self.chapters:
            return
            
        lines = self.chapters[self.current_chapter].split('\n')
        total_pages = (len(lines) // 50) + 1
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
        elif self.current_chapter < len(self.chapters) - 1:
            self.current_chapter += 1
            self.current_page = 0
        else:
            messagebox.showinfo("提示", "已经是最后一页了")
        
        self.display_chapter()
    
    def prev_page(self):
        """上一页"""
        if not self.chapters:
            return
            
        if self.current_page > 0:
            self.current_page -= 1
        elif self.current_chapter > 0:
            self.current_chapter -= 1
            lines = self.chapters[self.current_chapter].split('\n')
            total_pages = (len(lines) // 50) + 1
            self.current_page = total_pages - 1
        else:
            messagebox.showinfo("提示", "已经是第一页了")
        
        self.display_chapter()
    
    def show_toc(self):
        """显示目录"""
        if not self.chapters:
            messagebox.showwarning("警告", "请先打开EPUB文件")
            return
            
        toc_window = tk.Toplevel(self.root)
        toc_window.title("目录")
        toc_window.geometry("400x500")
        
        scrollbar = ttk.Scrollbar(toc_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            toc_window,
            yscrollcommand=scrollbar.set,
            font=('Microsoft YaHei', 11)
        )
        
        for i, chapter in enumerate(self.chapters):
            preview = chapter[:50].replace('\n', ' ')
            listbox.insert(tk.END, f"第{i+1}章: {preview}...")
        
        listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        def on_select(event):
            selection = listbox.curselection()
            if selection:
                self.current_chapter = selection[0]
                self.current_page = 0
                self.display_chapter()
                toc_window.destroy()
        
        listbox.bind('<Double-Button-1>', on_select)
    
    def manage_bookmarks(self):
        """管理书签"""
        bm_window = tk.Toplevel(self.root)
        bm_window.title("书签管理")
        bm_window.geometry("400x300")
        
        # 书签列表
        listbox = tk.Listbox(bm_window, font=('Microsoft YaHei', 11))
        listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for name in self.bookmarks:
            chap, page = self.bookmarks[name]
            listbox.insert(tk.END, f"{name} (第{chap+1}章-第{page+1}页)")
        
        # 按钮框架
        btn_frame = ttk.Frame(bm_window)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="添加", command=lambda: self.add_bookmark(bm_window)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="跳转", command=lambda: self.goto_bookmark(bm_window, listbox)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除", command=lambda: self.delete_bookmark(bm_window, listbox)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="关闭", command=bm_window.destroy).pack(side=tk.RIGHT)
    
    def add_bookmark(self, parent=None):
        """添加书签"""
        if not self.chapters:
            messagebox.showwarning("警告", "没有可添加书签的内容")
            return
            
        dialog = tk.Toplevel(self.root if parent is None else parent)
        dialog.title("添加书签")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="书签名称:").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.pack(pady=5, padx=10, fill=tk.X)
        
        def save_bookmark():
            name = entry.get().strip()
            if name:
                self.bookmarks[name] = (self.current_chapter, self.current_page)
                dialog.destroy()
                if parent:
                    parent.destroy()
                    self.manage_bookmarks()
            else:
                messagebox.showwarning("警告", "书签名称不能为空")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="保存", command=save_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
    
    def goto_bookmark(self, parent, listbox):
        """跳转到书签"""
        selection = listbox.curselection()
        if selection:
            name = list(listbox.get(selection[0]).split())[0]
            if name in self.bookmarks:
                self.current_chapter, self.current_page = self.bookmarks[name]
                self.display_chapter()
                parent.destroy()
    
    def delete_bookmark(self, parent, listbox):
        """删除书签"""
        selection = listbox.curselection()
        if selection:
            name = list(listbox.get(selection[0]).split())[0]
            if name in self.bookmarks:
                del self.bookmarks[name]
                parent.destroy()
                self.manage_bookmarks()
    
    def show_search(self):
        """显示搜索框"""
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)
        self.search_entry.focus()
    
    def hide_search(self):
        """隐藏搜索框"""
        self.search_frame.pack_forget()
    
    def do_search(self):
        """执行搜索"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
            
        self.search_results = []
        for i, chapter in enumerate(self.chapters):
            if keyword.lower() in chapter.lower():
                # 找到所有匹配位置
                start = 0
                while True:
                    pos = chapter.lower().find(keyword.lower(), start)
                    if pos == -1:
                        break
                    
                    preview = chapter[max(0, pos-20):pos+50].replace('\n', ' ')
                    self.search_results.append((i, pos, preview))
                    start = pos + 1
        
        if not self.search_results:
            messagebox.showinfo("提示", "没有找到匹配内容")
            return
            
        self.show_search_results()
    
    def show_search_results(self):
        """显示搜索结果"""
        result_window = tk.Toplevel(self.root)
        result_window.title("搜索结果")
        result_window.geometry("600x400")
        
        # 搜索结果列表
        tree = ttk.Treeview(result_window, columns=('preview'), show='headings')
        tree.heading('#0', text='位置')
        tree.heading('preview', text='内容预览')
        
        for i, (chap_idx, pos, preview) in enumerate(self.search_results):
            tree.insert('', tk.END, text=f"第{chap_idx+1}章", values=(f"...{preview}...",))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 跳转按钮
        def goto_result():
            selection = tree.selection()
            if selection:
                idx = tree.index(selection[0])
                chap_idx = self.search_results[idx][0]
                self.current_chapter = chap_idx
                self.current_page = 0
                self.display_chapter()
                result_window.destroy()
        
        btn_frame = ttk.Frame(result_window)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="跳转", command=goto_result).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="关闭", command=result_window.destroy).pack(side=tk.RIGHT)
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.geometry("400x300")
        
        # 字体设置
        ttk.Label(dialog, text="字体大小:").pack(pady=5)
        font_size = ttk.Combobox(dialog, values=[10, 12, 14, 16, 18, 20])
        font_size.pack(pady=5)
        font_size.set(12)
        
        # 主题设置
        ttk.Label(dialog, text="界面主题:").pack(pady=5)
        theme = ttk.Combobox(dialog, values=['litera', 'cosmo', 'minty', 'darkly'])
        theme.pack(pady=5)
        theme.set('litera')
        
        def apply_settings():
            new_size = int(font_size.get())
            new_theme = theme.get()
            
            self.text_area.config(font=('Microsoft YaHei', new_size))
            self.style.theme_use(new_theme)
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="应用", command=apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernEPubReader(root)
    root.mainloop()
