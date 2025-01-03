import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import similarityDetect
import gptDetect
import os
import json

similar_results = []

def show_results():
    result_win = tk.Toplevel()
    result_win.title("查重结果")
    result_win.geometry("1000x618")
    result_win.resizable(False, False)
    
    ITEMS_PER_PAGE = 10
    current_page = tk.IntVar(value=1)
    total_pages = (len(similar_results) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    # 创建主 frame
    main_frame = ttk.Frame(result_win)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # 创建带滚动条的列表区域
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    list_frame = ttk.Frame(canvas)

    # 配置 canvas
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # 打包滚动条和 canvas
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # 在canvas上创建窗口
    canvas.create_window((0, 0), window=list_frame, anchor="nw")

    def update_page():
        # 清空当前显示
        for widget in list_frame.winfo_children():
            widget.destroy()

        # 计算当前页的数据范围
        start_idx = (current_page.get() - 1) * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(similar_results))

        # 显示当前页的文件对列表
        for i, item in enumerate(similar_results[start_idx:end_idx]):
            row_frame = ttk.Frame(list_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            label_text = f"{os.path.basename(item['file1'])} - {os.path.basename(item['file2'])} (相似度: {item['similarity']}%)"
            ttk.Label(row_frame, text=label_text).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(row_frame, text="预览", 
                      command=lambda idx=start_idx+i: preview_pair(idx)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(row_frame, text="判为不重复", 
                      command=lambda idx=start_idx+i: remove_pair(idx, result_win)).pack(side=tk.LEFT, padx=5)

        # 更新页码显示和按钮状态
        page_label.config(text=f"第 {current_page.get()} 页 / 共 {total_pages} 页")
        prev_btn["state"] = "normal" if current_page.get() > 1 else "disabled"
        next_btn["state"] = "normal" if current_page.get() < total_pages else "disabled"
        
        # 更新canvas滚动区域
        list_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    # 分页控制栏
    control_frame = ttk.Frame(result_win)
    control_frame.pack(fill=tk.X, pady=5)

    def prev_page():
        if current_page.get() > 1:
            current_page.set(current_page.get() - 1)
            update_page()

    def next_page():
        if current_page.get() < total_pages:
            current_page.set(current_page.get() + 1)
            update_page()

    prev_btn = ttk.Button(control_frame, text="上一页", command=prev_page)
    prev_btn.pack(side=tk.LEFT, padx=5)

    page_label = ttk.Label(control_frame, text=f"第 1 页 / 共 {total_pages} 页")
    page_label.pack(side=tk.LEFT, padx=5)

    next_btn = ttk.Button(control_frame, text="下一页", command=next_page)
    next_btn.pack(side=tk.LEFT, padx=5)

    # 导出按钮
    export_btn = ttk.Button(result_win, text="导出", command=export_results)
    export_btn.pack(pady=5)

    # 显示第一页
    update_page()

def preview_pair(idx):
    pair = similar_results[idx]
    preview_win = tk.Toplevel()
    preview_win.title("预览")

    left_text = tk.Text(preview_win, width=50, height=30)
    left_text.grid(row=0, column=0, padx=5, pady=5)
    right_text = tk.Text(preview_win, width=50, height=30)
    right_text.grid(row=0, column=1, padx=5, pady=5)

    try:
        with open(pair["file1"], "r", encoding="utf-8") as f1:
            left_text.insert(tk.END, f1.read())
        with open(pair["file2"], "r", encoding="utf-8") as f2:
            right_text.insert(tk.END, f2.read())
    except:
        pass

    close_btn = ttk.Button(preview_win, text="关闭", command=preview_win.destroy)
    close_btn.grid(row=1, column=0, padx=5, pady=5, sticky="w")

def remove_pair(idx, parent_win):
    similar_results.pop(idx)
    parent_win.destroy()
    show_results()

def export_results():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if not file_path:
        return
    with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["file1", "file2", "similarity"])
        for item in similar_results:
            writer.writerow([item["file1"], item["file2"], item["similarity"]])
    messagebox.showinfo("导出", "结果已导出!")

def show_main_window():
    root = tk.Tk()
    root.title("ZH Code Checker")

    # 菜单
    menu_bar = tk.Menu(root)
    mode_menu = tk.Menu(menu_bar, tearoff=0)
    mode_menu.add_command(label="相似度检测模式", command=lambda: open_similarity_ui(root))
    mode_menu.add_command(label="GPT判定模式", command=lambda: open_gpt_ui(root))
    menu_bar.add_cascade(label="模式选择", menu=mode_menu)
    root.config(menu=menu_bar)

    root.mainloop()

def open_similarity_ui(root):
    for widget in root.winfo_children():
        if not isinstance(widget, tk.Menu):
            widget.destroy()

    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    # 目录选择
    dir_label = ttk.Label(frame, text="选择代码目录:")
    dir_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    dir_var = tk.StringVar()
    dir_entry = ttk.Entry(frame, textvariable=dir_var, width=50)
    dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    def choose_directory():
        path = filedialog.askdirectory()
        if path:
            dir_var.set(path)

    dir_btn = ttk.Button(frame, text="浏览", command=choose_directory)
    dir_btn.grid(row=0, column=2, padx=5, pady=5, sticky="w")

    # 后缀名
    suffix_label = ttk.Label(frame, text="后缀名:")
    suffix_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    suffix_var = tk.StringVar(value=".cpp")
    suffix_entry = ttk.Entry(frame, textvariable=suffix_var)
    suffix_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # 阈值
    threshold_label = ttk.Label(frame, text="查重阈值(%):")
    threshold_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
    threshold_var = tk.DoubleVar(value=90.0)
    threshold_entry = ttk.Entry(frame, textvariable=threshold_var)
    threshold_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    # 进度条与统计信息
    progress_label = ttk.Label(frame, text="进度:")
    progress_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
    progress_bar = ttk.Progressbar(frame, length=200)
    progress_bar.grid(row=3, column=1, padx=5, pady=5, sticky="w")

    info_var = tk.StringVar(value="已检测: 0/0  |  发现相似对: 0")
    info_label = ttk.Label(frame, textvariable=info_var)
    info_label.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

    # 开始检测
    def start_detection():
        global similar_results
        folder = dir_var.get()
        suffix = suffix_var.get()
        threshold = threshold_var.get()
        # 重置进度
        progress_bar["value"] = 0
        info_var.set("正在检测...")
        
        def update_progress(current, total, similar_count):
            val = int((current / total) * 100)
            progress_bar["value"] = val
            progress_bar.update()
            info_var.set(f"已检测: {current}/{total}对 | 发现相似: {similar_count}对")
            root.update()
            
        similar_results = similarityDetect.run_similarity_check(
            folder, suffix, threshold, 
            progress_callback=update_progress
        )
        
        info_var.set(f"检测完成 | 发现相似: {len(similar_results)}对")

    detect_btn = ttk.Button(frame, text="开始检测", command=start_detection)
    detect_btn.grid(row=5, column=0, padx=5, pady=5, sticky="w")
    
    result_btn = ttk.Button(frame, text="查看查重结果", command=show_results)
    result_btn.grid(row=5, column=1, padx=5, pady=5, sticky="w")

gpt_results = []

def show_gpt_results():
    result_win = tk.Toplevel()
    result_win.title("GPT检测结果")
    result_win.geometry("1000x618")
    result_win.resizable(False, False)
    
    ITEMS_PER_PAGE = 10
    current_page = tk.IntVar(value=1)
    total_pages = (len(gpt_results) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    main_frame = ttk.Frame(result_win)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    list_frame = ttk.Frame(canvas)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas.create_window((0, 0), window=list_frame, anchor="nw")

    def update_page():
        for widget in list_frame.winfo_children():
            widget.destroy()

        start_idx = (current_page.get() - 1) * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(gpt_results))

        for i, item in enumerate(gpt_results[start_idx:end_idx]):
            row_frame = ttk.Frame(list_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            result = json.loads(item["result"])
            label_text = f"{os.path.basename(item['file'])} (GPT概率: {result['probability']*100:.1f}%)"
            ttk.Label(row_frame, text=label_text).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(row_frame, text="预览", 
                      command=lambda idx=start_idx+i: preview_gpt(idx)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(row_frame, text="取消判定GPT生成", 
                      command=lambda idx=start_idx+i: remove_gpt(idx, result_win)).pack(side=tk.LEFT, padx=5)

        page_label.config(text=f"第 {current_page.get()} 页 / 共 {total_pages} 页")
        prev_btn["state"] = "normal" if current_page.get() > 1 else "disabled"
        next_btn["state"] = "normal" if current_page.get() < total_pages else "disabled"
        
        list_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    control_frame = ttk.Frame(result_win)
    control_frame.pack(fill=tk.X, pady=5)

    def prev_page():
        if current_page.get() > 1:
            current_page.set(current_page.get() - 1)
            update_page()

    def next_page():
        if current_page.get() < total_pages:
            current_page.set(current_page.get() + 1)
            update_page()

    prev_btn = ttk.Button(control_frame, text="上一页", command=prev_page)
    prev_btn.pack(side=tk.LEFT, padx=5)

    page_label = ttk.Label(control_frame, text=f"第 1 页 / 共 {total_pages} 页")
    page_label.pack(side=tk.LEFT, padx=5)

    next_btn = ttk.Button(control_frame, text="下一页", command=next_page)
    next_btn.pack(side=tk.LEFT, padx=5)

    export_btn = ttk.Button(result_win, text="导出", command=export_gpt_results)
    export_btn.pack(pady=5)

    update_page()

def preview_gpt(idx):
    item = gpt_results[idx]
    preview_win = tk.Toplevel()
    preview_win.title("预览")

    code_text = tk.Text(preview_win, width=100, height=30)
    code_text.pack(padx=5, pady=5)

    try:
        with open(item["file"], "r", encoding="utf-8") as f:
            code_text.insert(tk.END, f.read())
        
        result = json.loads(item["result"])
        analysis_text = tk.Text(preview_win, width=100, height=10)
        analysis_text.pack(padx=5, pady=5)
        analysis_text.insert(tk.END, f"GPT生成概率: {result['probability']*100:.1f}%\n\n检测依据:\n")
        for reason in result["reasons"]:
            analysis_text.insert(tk.END, f"- {reason}\n")
    except:
        pass

    close_btn = ttk.Button(preview_win, text="关闭", command=preview_win.destroy)
    close_btn.pack(pady=5)

def remove_gpt(idx, parent_win):
    gpt_results.pop(idx)
    parent_win.destroy()
    show_gpt_results()

def export_gpt_results():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if not file_path:
        return
    with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["file", "probability", "reasons"])
        for item in gpt_results:
            result = json.loads(item["result"])
            writer.writerow([item["file"], result["probability"], "; ".join(result["reasons"])])
    messagebox.showinfo("导出", "结果已导出!")

def open_gpt_ui(root):
    for widget in root.winfo_children():
        if not isinstance(widget, tk.Menu):
            widget.destroy()

    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    # 目录选择
    dir_label = ttk.Label(frame, text="选择代码目录:")
    dir_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    dir_var = tk.StringVar()
    dir_entry = ttk.Entry(frame, textvariable=dir_var, width=50)
    dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    def choose_directory():
        path = filedialog.askdirectory()
        if path:
            dir_var.set(path)

    dir_btn = ttk.Button(frame, text="浏览", command=choose_directory)
    dir_btn.grid(row=0, column=2, padx=5, pady=5, sticky="w")

    # 后缀名
    suffix_label = ttk.Label(frame, text="后缀名:")
    suffix_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    suffix_var = tk.StringVar(value=".cpp")
    suffix_entry = ttk.Entry(frame, textvariable=suffix_var)
    suffix_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # 阈值
    threshold_label = ttk.Label(frame, text="GPT判定阈值(%):")
    threshold_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
    threshold_var = tk.DoubleVar(value=50.0)
    threshold_entry = ttk.Entry(frame, textvariable=threshold_var)
    threshold_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    # 进度条与统计信息
    progress_label = ttk.Label(frame, text="进度:")
    progress_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
    progress_bar = ttk.Progressbar(frame, length=200)
    progress_bar.grid(row=3, column=1, padx=5, pady=5, sticky="w")

    info_var = tk.StringVar(value="已检测: 0个文件 | 发现GPT生成: 0个")
    info_label = ttk.Label(frame, textvariable=info_var)
    info_label.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

    def start_detection():
        global gpt_results
        gpt_results = []
        folder = dir_var.get()
        suffix = suffix_var.get()
        threshold = threshold_var.get() / 100
        
        files = [f for f in glob.glob(os.path.join(folder, f"*{suffix}"))]
        total = len(files)
        detected = 0
        
        progress_bar["value"] = 0
        for i, file in enumerate(files):
            result = gptDetect.detect_gpt_cpp(file)
            res_obj = json.loads(result)
            if res_obj["probability"] >= threshold:
                gpt_results.append({"file": file, "result": result})
                detected = len(gpt_results)
            progress_bar["value"] = (i + 1) / total * 100
            info_var.set(f"已检测: {i+1}/{total}个文件 | 发现GPT生成: {detected}个")
            root.update()

    detect_btn = ttk.Button(frame, text="开始检测", command=start_detection)
    detect_btn.grid(row=5, column=0, padx=5, pady=5, sticky="w")
    
    result_btn = ttk.Button(frame, text="查看检测结果", command=show_gpt_results)
    result_btn.grid(row=5, column=1, padx=5, pady=5, sticky="w")

if __name__ == "__main__":
    show_main_window()
