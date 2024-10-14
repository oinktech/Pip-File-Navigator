import os
import requests
import tarfile
import tempfile
import shutil
import logging
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

PYPI_BASE_URL = "https://pypi.org/pypi/{}/json"
TEMP_DIR = tempfile.mkdtemp()

# 日誌設置
logging.basicConfig(level=logging.INFO)
logging.info(f"Temporary directory created at: {TEMP_DIR}")

# 存放解壓縮後文件的全局變數
extracted_dirs = {}

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

                # 如果是 tar.gz 文件，解壓縮後顯示內容
                if file_ext == 'gz' and file_name.endswith('.tar.gz'):
                    extracted_dir = os.path.join(TEMP_DIR, file_name.split('.')[0])
                    with tarfile.open(temp_file_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(extracted_dir)

                    # 記錄解壓縮的目錄，以便後續刪除
                    extracted_dirs[file_name] = extracted_dir

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

# 刪除解壓縮後的文件
@app.route('/delete')
def delete_temp_files():
    # 刪除所有記錄的解壓縮目錄
    for directory in extracted_dirs.values():
        if os.path.exists(directory):
            shutil.rmtree(directory)
    extracted_dirs.clear()  # 清空記錄
    return redirect(url_for('index'))

# 下載解壓縮後的文件
@app.route('/download/<path:filename>')
def download_file(filename):
    # 打印當前TEMP_DIR中的文件
    logging.info(f"Attempting to download {filename} from {TEMP_DIR}")
    return send_from_directory(directory=TEMP_DIR, path=filename, as_attachment=True)

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
