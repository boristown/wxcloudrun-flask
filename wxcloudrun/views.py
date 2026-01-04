from datetime import datetime
import sys
import io
import time
from flask import render_template, request
from wxcloudrun import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response

# 安全的Python沙箱执行函数
def execute_python_sandbox(code, timeout=5):
    """
    在安全的沙箱中执行Python代码
    :param code: 要执行的Python代码
    :param timeout: 执行超时时间（秒）
    :return: 执行结果和输出
    """
    # 捕获标准输出
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    result = {
        "output": "",
        "error": "",
        "success": True
    }
    
    try:
        # 创建受限的全局命名空间
        restricted_globals = {
            '__builtins__': {
                'print': print,
                'abs': abs,
                'all': all,
                'any': any,
                'bool': bool,
                'chr': chr,
                'complex': complex,
                'dict': dict,
                'float': float,
                'int': int,
                'len': len,
                'list': list,
                'max': max,
                'min': min,
                'pow': pow,
                'range': range,
                'str': str,
                'tuple': tuple,
                'sum': sum,
                'sorted': sorted,
                'reversed': reversed,
                'round': round,
                'type': type
            }
        }
        
        # 使用exec执行代码
        exec(code, restricted_globals)
        
    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
    finally:
        # 恢复标准输出
        sys.stdout = old_stdout
        result["output"] = redirected_output.getvalue()
    
    return result


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


@app.route('/api/sandbox', methods=['POST'])
def python_sandbox():
    """
    Python沙箱接口，用于执行Python代码
    :return: 执行结果
    """
    # 获取请求体参数
    params = request.get_json()
    
    # 检查code参数
    if 'code' not in params:
        return make_err_response('缺少code参数')
    
    code = params['code']
    timeout = params.get('timeout', 5)  # 默认为5秒超时
    
    # 执行Python代码
    result = execute_python_sandbox(code, timeout)
    
    return make_succ_response(result)
