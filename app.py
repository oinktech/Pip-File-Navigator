import os
import pkgutil
from flask import Flask, render_template, request, redirect, url_for, send_file, abort

app = Flask(__name__)

# 首頁
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        module_name = request.form.get('module_name')
        if module_name:
            try:
                # 搜尋該模組的所有檔案
                module = __import__(module_name)
                files = [module.__file__]
                if not files:
                    return render_template('index.html', error="找不到此模組檔案")
                return render_template('files.html', files=files, module_name=module_name)
            except ImportError:
                return render_template('index.html', error="找不到模組，請檢查名稱是否正確。")
        else:
            return render_template('index.html', error="請輸入模組名稱")
    return render_template('index.html')

# 顯示檔案內容
@app.route('/file')
def view_file():
    file_path = request.args.get('path')
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return render_template('file_view.html', content=content, file_path=file_path)
    return redirect(url_for('index'))

# 錯誤處理 404
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="404: 找不到頁面"), 404

# 錯誤處理 500
@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="500: 伺服器內部錯誤"), 500

if __name__ == '__main__':
    app.run(debug=True,port=10000, host='0.0.0.0')
