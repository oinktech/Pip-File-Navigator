import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

PYPI_BASE_URL = "https://pypi.org/pypi/{}/json"

# 首頁
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        module_name = request.form.get('module_name')
        if module_name:
            try:
                # 呼叫 PyPI API 取得模組資訊
                response = requests.get(PYPI_BASE_URL.format(module_name))
                if response.status_code == 200:
                    module_data = response.json()
                    files = module_data['urls']
                    if not files:
                        return render_template('index.html', error="找不到此模組檔案")
                    return render_template('files.html', files=files, module_name=module_name)
                else:
                    return render_template('index.html', error="找不到模組，請檢查名稱是否正確。")
            except Exception as e:
                return render_template('index.html', error=f"無法查詢模組：{str(e)}")
        else:
            return render_template('index.html', error="請輸入模組名稱")
    return render_template('index.html')

# 顯示檔案內容
@app.route('/file')
def view_file():
    file_url = request.args.get('url')
    file_name = request.args.get('filename')
    if file_url:
        try:
            response = requests.get(file_url)
            if response.status_code == 200:
                content = response.text
                return render_template('file_view.html', content=content, file_name=file_name)
            else:
                return render_template('error.html', error="無法讀取檔案內容")
        except Exception as e:
            return render_template('error.html', error=f"無法讀取檔案：{str(e)}")
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
    app.run(debug=True,host='0.0.0.0',port=10000)
