import re
import json


def detect_gpt_cpp(cpp_file_path):
    try:
        with open(cpp_file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        return -1, [f"文件读取错误: {str(e)}"]

    features = {}
    reasons = []

    # 1. 注释特征
    single_comments = len(re.findall(r'//.*$', code, re.MULTILINE))
    multi_comments = len(re.findall(r'/\*.*?\*/', code, re.DOTALL))
    
    # issue #1: 忽略代码尾部空行
    lines = code.split('\n')
    while lines and not lines[-1].strip():
        lines.pop()
    total_lines = len(lines) or 1
    features['comment_ratio'] = (
        single_comments + multi_comments) / total_lines

    # 2. 变量命名规范
    camel_case = len(re.findall(
        r'\b[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b', code))
    snake_case = len(re.findall(r'\b[a-z][a-z0-9]*(_[a-z0-9]+)+\b', code))
    all_vars = len(re.findall(
        r'\b(?:int|float|double|char|bool|string)\s+([a-zA-Z_]\w*)', code))
    features['naming_consistency'] = (
        camel_case + snake_case) / (all_vars or 1)

    # 3. 代码结构特征
    features['avg_line_length'] = sum(
        len(line.strip()) for line in lines) / total_lines
    features['empty_line_ratio'] = len(
        [line for line in lines if not line.strip()]) / total_lines
    features['total_lines'] = total_lines
    
    # 4. 函数特征
    features['function_count'] = len(
        re.findall(r'\w+\s+\w+\s*\([^)]*\)\s*{', code))
    features['template_usage'] = 'template' in code.lower()

    # 5. C++特有特征
    features['stl_usage'] = bool(
        re.search(r'#include\s*<(vector|string|map|set|queue|stack)', code))
    features['class_usage'] = 'class' in code

    # 检测前置自增/自减
    features['prefix_inc_dec'] = len(re.findall(r'[^+\-](?:\+\+|--)[a-zA-Z_]\w*', code))
    features['postfix_inc_dec'] = len(re.findall(r'[a-zA-Z_]\w*(?:\+\+|--)', code))
    
    # 检测是否使用 bits/stdc++.h
    features['bits_header'] = '<bits/stdc++.h>' in code
    
    # 检测是否有多个 #include
    features['multiple_includes'] = len(re.findall(r'#include', code)) > 2
    
    # 评分系统
    score = 0
    max_score = 14.0 

    # 注释比例检查
    if 0.1 <= features['comment_ratio'] <= 0.3:
        score += 2
        reasons.append("注释密度合理，符合GPT风格")
    elif features['comment_ratio'] > 0.3:
        score += 1.5
        reasons.append("注释可能过多")

    # 命名规范一致性
    if features['naming_consistency'] > 0.7:
        score += 2
        reasons.append("变量命名风格高度统一")

    # 行长度检查
    if 30 <= features['avg_line_length'] <= 80:
        score += 1
        reasons.append("代码行长度规范")

    # 空行比例
    if 0.2 <= features['empty_line_ratio'] <= 0.3 and features['total_lines'] >= 20:
        score += 3
        reasons.append("空行分布合理")

    # STL使用检查
    if features['stl_usage']:
        score += 1
        reasons.append("使用STL库，代码现代化")

    # 模板使用检查
    if features['template_usage']:
        score -= 1

    # 前置自增/自减检查
    if features['prefix_inc_dec'] > features['postfix_inc_dec']:
        score += 3
        reasons.append("偏好使用前置自增/自减运算符，符合现代C++规范，疑似GPT生成")
    
    # bits/stdc++.h检查
    if not features['bits_header']:
        score += 3
        reasons.append("未使用bits/stdc++.h，遵循标准包含规范，疑似GPT生成")

    probability = score / max_score

    # 额外启发式规则
    if features['function_count'] >= 4 and probability > 0.5:
        probability += 0.1
        reasons.append("函数划分清晰，疑似GPT生成")

    if features['multiple_includes']:
        probability += 0.2
        reasons.append("存在多个#include，疑似GPT生成")
    probability = min(probability, 1.0)

    result = {
        "probability": probability,
        "reasons": reasons,
        "score": score,
        "max_score": max_score,
        "features": features
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)

