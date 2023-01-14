import os
import io
import string
import tkinter as tk
from tkinter.messagebox import showerror, askyesno
from tkinter.filedialog import asksaveasfilename, askopenfilename
from tkinter.scrolledtext import ScrolledText

from .src.constants import BUILTINS, KEYWORDS
from .src.basic import run

WIDTH, HEIGHT = 1000, 600
PAGE_LINES = 24
THEMES = {
    '默认': '#000000.#FFFFFF',
    '灰色': '#83406A.#D1D4D1',
    '碧蓝': '#5B8340.#D1E7E0',
    '粗褐': '#4B4620.#FFF0E1',
    '钴蓝': '#ffffBB.#3333AA',
    '橄榄绿': '#D1E7E0.#5B8340',
    '夜间': '#FFFFFF.#000000'
}


def should_fill(line: str):
    line = line.strip()
    if line.endswith('then') or line.startswith(('namespace', 'case', 'default', 'try', 'else', 'finally')):
        return True
    if 'then' in line and line.split('#')[0].rstrip().endswith('then'):
        return True
    if line.startswith('function') and ('do' not in line):
        return True
    return False


class IDE_CN(object):
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('KittenIDE')
        self.root.resizable(False, False)
        self.root.geometry(
            '%dx%d+%d+%d' % (
                WIDTH, HEIGHT,
                (self.root.winfo_screenwidth() - WIDTH) / 2,
                (self.root.winfo_screenheight() - HEIGHT) / 2,
            )
        )
        self.root.protocol('WM_DELETE_WINDOW', self.exit)
        self.project_path = None
        self.project_name = None
        
        self.edit_frame = tk.Frame(self.root)
        self.line_text = tk.Text(self.edit_frame, state=tk.DISABLED, width=6, padx=3, takefocus=0,
                                 border=0, background='khaki', wrap=tk.NONE, font=('consoles', 13))
        self.line_text.pack(side=tk.LEFT, fill=tk.Y)
        
        self.content_text = tk.Text(self.edit_frame, wrap=tk.WORD, undo=True, font=('consoles', 13))
        self.text_scroll_bar = tk.Scrollbar(self.edit_frame)
        self.content_text.config(yscrollcommand=self.on_scroll)
        self.text_scroll_bar.config(command=self.content_text.yview)
        self.text_scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.pack(expand=tk.YES, fill=tk.BOTH)
        self.char_info = tk.Label(self.content_text, text='行: 1 | 列: 1', font=('consoles', 12),
                                  background='gray')
        self.char_info.pack(expand=tk.NO, fill=None, side=tk.RIGHT, anchor=tk.SE)
        
        self.edit_frame.pack(expand=tk.YES, fill=tk.BOTH)
        
        self.run_text = ScrolledText(self.root, background='light gray', height=180,
                                     state=tk.DISABLED, wrap=tk.WORD, font=('consoles', 13))
        self.run_text.pack(expand=tk.YES, fill=tk.BOTH)
        
        self.content_text.bind('<Any-KeyPress>', self.on_content_changed)
        self.content_text.bind('<Button-1>', self.on_content_changed)
        self.content_text.bind('<Button-3>', self.show_popup_menu)
        self.content_text.bind('<KeyRelease>', self.render_code)
        
        self.init_menu()
        self.root.config(menu=self.menu_bar)
        
        self.file = None
    
    def init_menu(self):
        self.popup_menu = tk.Menu(self.content_text, tearoff=0)
        self.popup_menu.add_command(label='剪切', compound=tk.LEFT, command=self.cut)
        self.popup_menu.add_command(label='复制', compound=tk.LEFT, command=self.copy)
        self.popup_menu.add_command(label='粘贴', compound=tk.LEFT, command=self.paste)
        self.popup_menu.add_command(label='撤销', compound=tk.LEFT, command=self.undo)
        self.popup_menu.add_command(label='重做', compound=tk.LEFT, command=self.redo)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='查找', compound=tk.LEFT, command=self.find_text)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='全选', compound=tk.LEFT, command=self.select_all)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label='退出', compound=tk.LEFT, command=self.exit)
        self.popup_menu.add_command(label='强制退出', compound=tk.LEFT, command=self.force_close)
        
        self.menu_bar = tk.Menu(self.root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.themes_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.run_menu = tk.Menu(self.menu_bar, tearoff=0)
        
        self.menu_bar.add_cascade(label='文件', menu=self.file_menu)
        self.menu_bar.add_cascade(label='编辑', menu=self.edit_menu)
        self.menu_bar.add_cascade(label='视图', menu=self.view_menu)
        self.menu_bar.add_cascade(label='运行', menu=self.run_menu)
        
        self.file_menu.add_command(label='新建', accelerator='Ctrl+N', compound=tk.LEFT,
                                   command=self.new_file)
        self.file_menu.add_command(label='打开', accelerator='Ctrl+O', compound=tk.LEFT,
                                   command=self.open_file)
        self.file_menu.add_command(label='保存', accelerator='Ctrl+S', compound=tk.LEFT,
                                   command=self.save)
        self.file_menu.add_command(label='另存为', accelerator='Ctrl+Shift+S',
                                   compound=tk.LEFT, command=self.save_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='退出', accelerator='Alt+F4', compound=tk.LEFT,
                                   command=self.exit)
        self.file_menu.add_command(label='强制退出', compound=tk.LEFT, command=self.force_close)
        
        self.edit_menu.add_command(label='撤销', accelerator='Ctrl+Z', compound=tk.LEFT,
                                   command=self.undo)
        self.edit_menu.add_command(label='重做', accelerator='Ctrl+Y', compound=tk.LEFT,
                                   command=self.redo)
        self.edit_menu.add_command(label='剪切', accelerator='Ctrl+X', compound=tk.LEFT,
                                   command=self.cut)
        self.edit_menu.add_command(label='复制', accelerator='Ctrl+C', compound=tk.LEFT,
                                   command=self.copy)
        self.edit_menu.add_command(label='粘贴', accelerator='Ctrl+V', compound=tk.LEFT,
                                   command=self.paste)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label='查找', accelerator='Ctrl+F', compound=tk.LEFT,
                                   command=self.find_text)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label='全选', accelerator='Ctrl+A',
                                   compound=tk.LEFT, command=self.select_all)
        
        self.show_line_number = tk.IntVar()
        self.show_line_number.set(1)
        self.view_menu.add_checkbutton(label='显示代码行数',
                                       variable=self.show_line_number,
                                       command=self.update_line_numbers)
        
        self.show_cursor_info = tk.IntVar()
        self.show_cursor_info.set(1)
        self.view_menu.add_checkbutton(label='在底部显示光标位置',
                                       variable=self.show_cursor_info,
                                       command=self.update_char_info)
        
        self.view_menu.add_cascade(label='主题', menu=self.themes_menu)
        self.themes_choices = tk.StringVar()
        self.themes_choices.set('默认')
        
        for k, theme in THEMES.items():
            self.themes_menu.add_radiobutton(label=k, variable=self.themes_choices,
                                             command=self.change_theme, value=k)
            
        self.run_menu.add_command(label='使用解释器...', command=self.run, compound=tk.LEFT)
        self.run_menu.add_command(label='编译为python3', compound=tk.LEFT)
        
        self.content_text.bind('<Control-y>', self.redo)  # handling Ctrl + small-case y
        self.content_text.bind('<Control-Y>', self.redo)  # handling Ctrl + upper-case Y
        self.content_text.bind('<Control-a>', self.select_all)  # handling Ctrl + upper-case a
        self.content_text.bind('<Control-A>', self.select_all)  # handling Ctrl + upper-case A
        self.content_text.bind('<Control-f>', self.find_text)  # ctrl + f
        self.content_text.bind('<Control-F>', self.find_text)  # ctrl + F
        self.content_text.bind('<Control-N>', self.new_file)  # ctrl + N
        self.content_text.bind('<Control-n>', self.new_file)  # ctrl + n
        self.content_text.bind('<Control-O>', self.open_file)  # ctrl + O
        self.content_text.bind('<Control-o>', self.open_file)  # ctrl + o
        self.content_text.bind('<Control-S>', self.save)  # ctrl + S
        self.content_text.bind('<Control-s>', self.save)  # ctrl + s
        self.content_text.bind('<Control-Shift-S>', self.save_as)  # ctrl + shift + S
        self.content_text.bind('<Control-Shift-s>', self.save_as)  # ctrl + shift + s
    
    def change_theme(self):
        selected_theme = self.themes_choices.get()
        fg_bg = THEMES.get(selected_theme)
        foreground, background = fg_bg.split('.')
        self.content_text.config(bg=background, fg=foreground)
    
    def on_scroll(self, *args):
        self.text_scroll_bar.set(*args)
    
    def show_popup_menu(self, event):
        self.popup_menu.tk_popup(event.x_root, event.y_root)
    
    def new_file(self, *_):
        if self.file:
            self.save()
        self.content_text.delete('0.0', tk.END)
        self.file = None
        self.root.title('未命名')
        self.on_content_changed(None)
    
    def open_file(self, *_):
        if self.file:
            self.save()
        file_path = askopenfilename(filetypes=[
            ('src File', '*.kst'),
            ('All Files', '*.*')
        ])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except (FileNotFoundError, FileExistsError):
                showerror('Error', f'file {file_path} not found')
            except UnicodeError:
                showerror('Error', 'unicode must be UTF-8')
            except PermissionError:
                showerror('Error', 'file is opening')
            except MemoryError:
                showerror('Error', 'content is too long')
            else:
                self.content_text.delete('0.0', tk.END)
                self.content_text.insert('0.0', text)
                self.file = file_path
                self.root.title(f'{os.path.basename(file_path)} - KittenIDE')
        self.on_content_changed(None)
        return 'break'
    
    def write_to_file(self, file):
        try:
            with open(file, 'w', encoding='utf-8') as fp:
                fp.write(self.content_text.get('0.0', tk.END))
        except (FileNotFoundError, FileExistsError):
            showerror('Error', f'file {self.file} not found')
        except UnicodeError:
            showerror('Error', 'unicode must be UTF-8')
        except PermissionError:
            showerror('Error', 'file is opening')
        except (Exception,) as err:
            showerror('Error', str(err))
        return 'break'
    
    def save(self, *_):
        if self.file:
            return self.write_to_file(self.file)
        self.save_as()
        return 'break'
    
    def save_as(self, *_):
        file = asksaveasfilename(defaultextension='.kst', filetypes=[
            ('KittenScript文件', '*.kst'),
            ('所有文件', '*.*')
        ])
        if file:
            self.file = file
            self.write_to_file(file)
            self.root.title(f'{os.path.basename(file)} - KittenIDE')
    
    def get_line_numbers(self):
        res = []
        # if self.show_line_number.get():
        if self.show_line_number.get():
            row, col = self.content_text.index(tk.END).split('.')
            for n in range(1, int(row)):
                res.append(str(n))
        if len(res) > PAGE_LINES:
            row, col = map(int, self.content_text.index(tk.INSERT).split('.'))
            if row == len(res):
                res = res[len(res) - PAGE_LINES:]
        return '\n'.join(res)
    
    def find_text(self):
        window = tk.Toplevel(self.root)
        window.title('查找')
        window.transient(self.root)
        window.resizable(False, False)
        find_text = tk.Label(window, text='查找所有:', font=('Consoles', 12))
        find_text.grid(row=0, column=0, sticky=tk.E)
        search_entry = tk.Entry(window, width=25)
        search_entry.grid(row=0, column=1, padx=2, pady=2, sticky=tk.EW)
        search_entry.focus_set()
        ignore_case_value = tk.IntVar()
        ignore_case = tk.Checkbutton(window, text='忽略大小写',
                                     variable=ignore_case_value, font=('Consoles', 12))
        ignore_case.grid(row=1, column=1, sticky=tk.E, padx=2, pady=2)
        find_all = tk.Button(window, text='查找所有', command=lambda: self.search_output(
            search_entry.get(),
            ignore_case_value.get(),
            window, search_entry
        ))
        find_all.grid(row=0, column=2, sticky=tk.EW, padx=2, pady=2)
        
        def close_search_window():
            self.content_text.tag_remove('match', '1.0', tk.END)
            window.destroy()
            return 'break'
        
        window.protocol('WM_DELETE_WINDOW', close_search_window)
    
    def search_output(self, needle, if_ignore_case, search_window, search_box):
        self.content_text.tag_remove('match', '1.0', tk.END)
        matches_found = 0
        if needle:
            start_pos = '1.0'
            while True:
                start_pos = self.content_text.search(needle, start_pos,
                                                     nocase=if_ignore_case,
                                                     stopindex=tk.END)
                if not start_pos:
                    break
                end_pos = '{}+{}c'.format(start_pos, len(needle))
                self.content_text.tag_add('match', start_pos, end_pos)
                matches_found += 1
                start_pos = end_pos
                self.content_text.tag_config('match', foreground='red',
                                             background='yellow')
                search_box.focus_set()
                search_window.title('{} matches found'.format(matches_found))
    
    def exit(self):
        if askyesno('提示', '确定退出吗?'):
            self.save()
            self.root.destroy()
    
    def force_close(self):
        if askyesno('警告', '强制关闭不会您的保存文件，确定关闭吗?'):
            self.root.destroy()
    
    def update_line_numbers(self):
        line_numbers = self.get_line_numbers()
        self.line_text.config(state=tk.NORMAL)
        self.line_text.delete('0.0', tk.END)
        if self.show_line_number.get():
            self.line_text.insert('0.0', line_numbers)
        self.line_text.config(state=tk.DISABLED)
    
    def update_char_info(self):
        row, col = self.content_text.index(tk.INSERT).split('.')
        line_num, col_num = str(int(row)), str(int(col) + 1)
        info_text = f'行: {line_num} | 列: {col_num}' if self.show_cursor_info.get() else ''
        self.char_info.config(text=info_text)
    
    def on_content_changed(self, _):
        self.update_line_numbers()
        self.update_char_info()
    
    def show(self):
        self.root.mainloop()
    
    def cut(self, *_):
        self.content_text.event_generate('<<Cut>>')
    
    def copy(self, *_):
        self.content_text.event_generate('<<Copy>>')
    
    def paste(self, *_):
        self.content_text.event_generate('<<Paste>>')
    
    def undo(self, *_):
        self.content_text.event_generate('<<Undo>>')
        return 'break'
    
    def redo(self, *_):
        self.content_text.event_generate('<<Redo>>')
        return 'break'
    
    def select_all(self, *_):
        self.content_text.tag_add('sel', '1.0', 'end')
        return 'break'
    
    def render_code(self, event):
        def is_num(w: str):
            for i in w:
                if i not in string.digits:
                    return False
            return True
        
        self.content_text.tag_config('bif', foreground='purple')
        self.content_text.tag_config('kw', foreground='blue')
        self.content_text.tag_config('com', foreground='dark red')
        self.content_text.tag_config('str', foreground='green')
        self.content_text.tag_config('num', foreground='dark blue')
        line, col = map(int, self.content_text.index(tk.INSERT).split('.'))
        if event.keycode == 9:  # press tab
            self.content_text.delete('{}.{}'.format(line, col - 1), tk.INSERT)
            self.content_text.insert(tk.INSERT, ' ' * 4)
            return
        if event.keycode == 13:  # press enter
            last_line = self.content_text.get('%d.0' % (line - 1), tk.INSERT).rstrip()
            n = len(last_line) - len(last_line.lstrip())
            if should_fill(last_line):
                n += 4
            if last_line.endswith(('break', 'continue', 'return', 'throw', 'pass', 'exit')):
                n -= 4
            self.content_text.insert(tk.INSERT, ' ' * n)
            return
        if event.keycode == 8:  # press backspace
            current = self.content_text.get('%d.0' % line, '%d.%d' % (line, col))
            n = min(3, len(current) - len(current.rstrip()))
            if n > 1:
                self.content_text.delete('%d.%d' % (line, col - n), tk.INSERT)
            return
        bifs = BUILTINS.copy()
        kw = KEYWORDS.copy()
        lines = self.content_text.get('0.0', tk.END).rstrip('\n').splitlines(keepends=True)
        self.content_text.delete('0.0', tk.END)
        start = 0
        pos = self.text_scroll_bar.get()
        wd = set(string.ascii_letters + string.digits + '_$')
        for one_line in lines:
            flag1 = flag2 = flag3 = flag4 = False
            for index, char in enumerate(one_line):
                if char == '"' and (not flag3) and (not flag4):
                    flag2 = not flag2
                    self.content_text.insert(tk.INSERT, char, 'str')
                elif char == "'" and (not flag2) and (not flag4):
                    flag3 = not flag3
                    self.content_text.insert(tk.INSERT, char, 'str')
                elif char == '`' and (not flag2) and (not flag3):
                    flag4 = not flag4
                    self.content_text.insert(tk.INSERT, char, 'str')
                elif flag2 or flag3 or flag4:
                    self.content_text.insert(tk.INSERT, char, 'str')
                else:
                    if char not in wd:
                        if flag1:
                            flag1 = False
                            word = one_line[start: index]
                            if word in bifs:
                                self.content_text.insert(tk.INSERT, word, 'bif')
                            elif word in kw:
                                self.content_text.insert(tk.INSERT, word, 'kw')
                            elif is_num(word):
                                self.content_text.insert(tk.INSERT, word, 'num')
                            else:
                                self.content_text.insert(tk.INSERT, word)
                        if char == '#':
                            self.content_text.insert(tk.INSERT, one_line[index:], 'com')
                            break
                        else:
                            self.content_text.insert(tk.INSERT, char)
                    else:
                        if not flag1:
                            flag1 = True
                            start = index
            if flag1:
                word = one_line[start:]
                if word in bifs:
                    self.content_text.insert(tk.INSERT, word, 'bif')
                elif word in kw:
                    self.content_text.insert(tk.INSERT, word, 'kw')
                elif is_num(word):
                    self.content_text.insert(tk.INSERT, word, 'num')
                else:
                    self.content_text.insert(tk.INSERT, word)

        self.content_text.yview_moveto(pos[1])
        self.content_text.mark_set(tk.INSERT, '%d.%d' % (line, col))

    def run(self, *_):
        stdout = io.StringIO()
        value, error, ctx = run(self.file or '<untitled>', self.content_text.get('0.0', tk.END), out_io=stdout)
        self.run_text.tag_config('err', foreground='red')
        self.run_text.tag_config('tip', foreground='blue')
        self.run_text.config(state=tk.NORMAL)
        self.run_text.delete('0.0', tk.END)
        if error:
            self.run_text.insert('0.0', error.as_string(), 'err')
        else:
            self.run_text.insert('0.0', stdout.getvalue())
        self.run_text.insert('0.0', '内部解释器环境已运行完成，结果或错误如下:\n\n', 'tip')
        self.run_text.config(state=tk.DISABLED)
        stdout.close()


if __name__ == '__main__':
    IDE_CN().show()
