import os
import glob
import json
import difflib

def check_two_files_similarity(file1, file2):
    try:
        # 提取 uid
        def get_uid(filename):
            try:
                return os.path.basename(filename).split('_')[0]
            except:
                return None
                
        uid1 = get_uid(file1)
        uid2 = get_uid(file2)
        
        # 检查 uid
        if not uid1 or not uid2:
            return json.dumps({
                "similarity": 0,
                "error": "无法提取uid"
            }, ensure_ascii=False, indent=2)
            
        # 相同 uid 返回0
        if uid1 == uid2:
            return json.dumps({
                "similarity": 0
            }, ensure_ascii=False, indent=2)
            
        # 计算相似度
        with open(file1, 'r', encoding='utf-8') as f1, \
             open(file2, 'r', encoding='utf-8') as f2:
            content1 = f1.read()
            content2 = f2.read()
            
        similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
        
        return json.dumps({
            "similarity": round(similarity * 100, 2)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "similarity": 0,
            "error": str(e)
        }, ensure_ascii=False, indent=2)

def run_similarity_check(folder_path, suffix, threshold, progress_callback=None):
    files = glob.glob(os.path.join(folder_path, f"*{suffix}"))
    total = len(files)
    results = []
    total_checks = (total * (total - 1)) // 2
    checks_done = 0
    similar_found = 0
    
    for i in range(total):
        for j in range(i + 1, total):
            file1 = files[i]
            file2 = files[j]
            similarity_data = json.loads(check_two_files_similarity(file1, file2))
            checks_done += 1
            
            if similarity_data.get("similarity", 0) >= threshold:
                results.append({
                    "file1": file1,
                    "file2": file2,
                    "similarity": similarity_data["similarity"]
                })
                similar_found += 1
                
            if progress_callback:
                progress_callback(checks_done, total_checks, similar_found)
                
    return results