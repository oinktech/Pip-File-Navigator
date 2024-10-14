import os
import requests
import zipfile
import tempfile
import shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

PYPI_BASE_URL = "https://pypi.org/pypi/{}/json"
TEMP_DIR = tempfile.mkdtemp()

# 檢查並創建臨時文件夾
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

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
            response = requests.get(file_url, stream=True)
            if response.status_code == 200:
                file_ext = file_name.split('.')[-1].lower()
                temp_file_path = os.path.join(TEMP_DIR, file_name)
                
                # 儲存檔案到臨時文件夾
                with open(temp_file_path, 'wb') as temp_file:
                    for chunk in response.iter_content(chunk_size=128):
                        temp_file.write(chunk)

                # 如果是 zip 文件，解壓縮後顯示內容
                if file_ext == 'zip':
                    extracted_dir = os.path.join(TEMP_DIR, file_name.split('.')[0])
                    with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                        zip_ref.extractall(extracted_dir)

                    # 列出解壓縮後的文件
                    extracted_files = os.listdir(extracted_dir)
                    return render_template('extracted_files.html', files=extracted_files, dir=extracted_dir, module_name=file_name)

                # 如果是普通文件，直接顯示內容
                with open(temp_file_path, 'r') as file:
                    content = file.read()
                    return render_template('file_view.html', content=content, file_name=file_name)
            
            else:
                return render_template('error.html', error="無法讀取檔案內容")
        except Exception as e:
            return render_template('error.html', error=f"無法讀取檔案：{str(e)}")
    
    return redirect(url_for('index'))

# 下載解壓縮後的文件
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(directory=TEMP_DIR, path=filename, as_attachment=True)

# 刪除臨時檔案
@app.route('/delete/<path:directory>')
def delete_temp_files(directory):
    # 刪除目錄
    full_path = os.path.join(TEMP_DIR, directory)
    if os.path.exists(full_path):
        shutil.rmtree(full_path)
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
    app.run(debug=True,port=10000,host='0.0.0.0')
