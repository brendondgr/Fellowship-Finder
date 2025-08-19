from flask import Flask, render_template, jsonify, request
from utils.data_manager import DataManager
import ast
import pandas as pd
import subprocess
import sys

app = Flask(__name__)
data_manager = DataManager()

@app.route("/")
def index():
    print(f"Index Data Availability: {data_manager.data_available}")
    return render_template("index.html")

@app.route("/api/fellowships", methods=['GET'])
def get_fellowships():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Extract filters from request arguments
    filters = {
        'min_stars': request.args.get('min_stars', 1, type=int),
        'favorites_first': request.args.get('favorites_first', 'false').lower() == 'true',
        'show_removed': request.args.get('show_removed', 'false').lower() == 'true',
        'keywords': [kw.strip() for kw in request.args.get('keywords', '').split(',') if kw.strip()]
    }

    fellowships_df = data_manager.get_filtered_fellowships(filters)
    total_count = len(fellowships_df)
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_fellowships = fellowships_df.iloc[start:end]
    
    paginated_fellowships = paginated_fellowships.where(pd.notnull(paginated_fellowships), None)
    fellowships_list = paginated_fellowships.reset_index().rename(columns={'index': 'id'}).to_dict('records')

    for fellowship in fellowships_list:
        subjects_raw = fellowship.get('subjects')
        if isinstance(subjects_raw, str):
            try:
                subjects_list = ast.literal_eval(subjects_raw)
                if isinstance(subjects_list, list):
                    fellowship['subjects'] = subjects_list
                else:
                    fellowship['subjects'] = [str(subjects_list)]
            except (ValueError, SyntaxError):
                fellowship['subjects'] = [s.strip() for s in subjects_raw.split(',') if s.strip()]
        elif not isinstance(subjects_raw, list):
            fellowship['subjects'] = []

    return jsonify({
        "fellowships": fellowships_list,
        "total_count": total_count,
        "has_more": end < total_count
    })

@app.route("/api/fellowships/<fellowship_id>/favorite", methods=['POST'])
def favorite_fellowship(fellowship_id):
    data = request.json
    favorited_status = data.get('favorited')
    success = data_manager.update_fellowship_status(fellowship_id, 'favorited', favorited_status)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route("/api/fellowships/<fellowship_id>/remove", methods=['POST'])
def remove_fellowship(fellowship_id):
    success = data_manager.update_fellowship_status(fellowship_id, 'show', 0)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route("/api/fellowships/<fellowship_id>/undo", methods=['POST'])
def undo_remove_fellowship(fellowship_id):
    success = data_manager.update_fellowship_status(fellowship_id, 'show', 1)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """
    Refreshes the data by checking for the processed data file and reloading it if necessary.
    """
    try:
        data_manager.refresh_data_if_needed()
        return jsonify({'success': True, 'message': 'Data refreshed successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/status", methods=['GET'])
def get_status():
    return jsonify({
        "data_available": data_manager.data_available,
        "message": "Processed fellowship data is available." if data_manager.data_available else "Processed fellowship data not found. Please process the raw data."
    })

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    cleanup = data.get('cleanup', False)
    browser = data.get('browser', 'firefox')

    command = [sys.executable, 'data_retrieval.py']
    if cleanup:
        command.append('--cleanup')
    
    command.append('--browser')
    command.append(browser)

    try:
        subprocess.Popen(command)
        return jsonify({'success': True, 'message': 'Scraping process started.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process():
    command = [sys.executable, 'data_retrieval.py', '--refine']
    try:
        subprocess.Popen(command)
        return jsonify({'success': True, 'message': 'Processing started.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
