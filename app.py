from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from utils.data_manager import DataManager
import ast
import pandas as pd
import subprocess
import sys
import json
import os

app = Flask(__name__)
app.secret_key = 'fellowship-helper-secret-key-change-in-production'
data_manager = DataManager()

@app.route("/")
def index():
    # Get filter and pagination parameters from URL
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    min_stars = request.args.get('min_stars', 1, type=int)
    favorites_first = request.args.get('favorites_first', 'false').lower() == 'true'
    show_removed = request.args.get('show_removed', 'false').lower() == 'true'
    keywords = request.args.get('keywords', '', type=str)
    
    print(f"Index Data Availability: {data_manager.data_available}")
    
    # If no data is available, render template with empty state
    if not data_manager.data_available:
        return render_template("index.html", 
                             fellowships=[],
                             total_count=0,
                             current_page=1,
                             per_page=per_page,
                             has_more=False,
                             has_previous=False,
                             filters={
                                 'min_stars': min_stars,
                                 'favorites_first': favorites_first,
                                 'show_removed': show_removed,
                                 'keywords': keywords
                             },
                             data_available=False)
    
    # Prepare filters for DataManager
    filters = {
        'min_stars': min_stars,
        'favorites_first': favorites_first,
        'show_removed': show_removed,
        'keywords': [kw.strip() for kw in keywords.split(',') if kw.strip()]
    }
    
    # Get filtered fellowships from DataManager with error handling
    try:
        fellowships_df = data_manager.get_filtered_fellowships(filters)
        total_count = len(fellowships_df)
        
        print(f"[Index] Filters={filters} | page={page} per_page={per_page} | total_count={total_count}")
        
        # Reset index and add ID column for template use
        fellowships_df = fellowships_df.reset_index().rename(columns={'index': 'id'})
    except Exception as e:
        print(f"[Index] Error filtering fellowships: {e}")
        flash(f'Error loading fellowship data: {str(e)}', 'error')
        return render_template("index.html", 
                             fellowships=[],
                             total_count=0,
                             current_page=1,
                             per_page=per_page,
                             has_more=False,
                             has_previous=False,
                             filters=filters,
                             data_available=False)
    
    # Calculate pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated_fellowships = fellowships_df.iloc[start:end]
    
    print(f"[Index] Slice start={start} end={end} | page_rows={len(paginated_fellowships)}")
    
    # Convert to template-friendly format
    fellowships_list = paginated_fellowships.where(pd.notnull(paginated_fellowships), None).to_dict('records')
    
    # Process subjects field for each fellowship
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
    
    # Handle invalid page numbers
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
    original_page = page
    
    if page < 1:
        page = 1
        if original_page != page:
            flash('Invalid page number. Redirected to first page.', 'warning')
    elif page > total_pages and total_pages > 0:
        page = total_pages
        if original_page != page:
            flash(f'Page {original_page} does not exist. Redirected to last page.', 'warning')
        # Recalculate pagination with corrected page
        start = (page - 1) * per_page
        end = start + per_page
        paginated_fellowships = fellowships_df.iloc[start:end]
        fellowships_list = paginated_fellowships.where(pd.notnull(paginated_fellowships), None).to_dict('records')
        
        # Reprocess subjects for corrected page
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
    
    # Calculate comprehensive pagination info
    has_more = end < total_count
    has_previous = page > 1
    next_page = page + 1 if has_more else None
    previous_page = page - 1 if has_previous else None
    
    # Create page range for pagination controls (show 5 pages around current)
    page_range = []
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)
    
    for p in range(start_page, end_page + 1):
        page_range.append(p)
    
    print(f"[Index] Returning {len(fellowships_list)} items | page={page}/{total_pages} | has_more={has_more} | has_previous={has_previous}")
    
    return render_template("index.html",
                        fellowships=fellowships_list,
                        total_count=total_count,
                        current_page=page,
                        per_page=per_page,
                        total_pages=total_pages,
                        has_more=has_more,
                        has_previous=has_previous,
                        next_page=next_page,
                        previous_page=previous_page,
                        page_range=page_range,
                        filters={
                            'min_stars': min_stars,
                            'favorites_first': favorites_first,
                            'show_removed': show_removed,
                            'keywords': keywords
                        },
                        data_available=data_manager.data_available)

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
    print(f"[GET /api/fellowships] Filters={filters} | page={page} per_page={per_page} | total_count={total_count}")

    fellowships_df = fellowships_df.reset_index().rename(columns={'index': 'id'})
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_fellowships = fellowships_df.iloc[start:end]
    print(f"[GET /api/fellowships] Slice start={start} end={end} | page_rows={len(paginated_fellowships)}")
    
    fellowships_list = paginated_fellowships.where(pd.notnull(paginated_fellowships), None).to_dict('records')

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
    print(f"[GET /api/fellowships] Returning {len(fellowships_list)} items | has_more={end < total_count}")

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

# New server-side fellowship action routes
@app.route("/fellowship/<fellowship_id>/favorite", methods=['POST'])
def favorite_fellowship_redirect(fellowship_id):
    """Toggle favorite status and redirect back with preserved filters"""
    # Get current favorite status and toggle it
    try:
        row_index = int(fellowship_id)
        if data_manager.df is not None and row_index in data_manager.df.index:
            current_status = data_manager.df.loc[row_index, 'favorited']
            new_status = 1 if current_status == 0 else 0
            success = data_manager.update_fellowship_status(fellowship_id, 'favorited', new_status)
            
            if success:
                action = "favorited" if new_status == 1 else "unfavorited"
                flash(f'Fellowship {action} successfully!', 'success')
            else:
                flash('Failed to update fellowship status.', 'error')
        else:
            flash('Fellowship not found.', 'error')
    except (ValueError, TypeError):
        flash('Invalid fellowship ID.', 'error')
    
    # Preserve current URL parameters and redirect back
    return redirect(request.referrer or url_for('index'))

@app.route("/fellowship/<fellowship_id>/remove", methods=['POST'])
def remove_fellowship_redirect(fellowship_id):
    """Remove fellowship and redirect back with preserved filters"""
    success = data_manager.update_fellowship_status(fellowship_id, 'show', 0)
    
    if success:
        flash('Fellowship removed successfully! You can undo this action.', 'success')
    else:
        flash('Failed to remove fellowship.', 'error')
    
    # Preserve current URL parameters and redirect back
    return redirect(request.referrer or url_for('index'))

@app.route("/fellowship/<fellowship_id>/undo", methods=['POST'])
def undo_remove_fellowship_redirect(fellowship_id):
    """Undo remove fellowship and redirect back with preserved filters"""
    success = data_manager.update_fellowship_status(fellowship_id, 'show', 1)
    
    if success:
        flash('Fellowship removal undone successfully!', 'success')
    else:
        flash('Failed to undo fellowship removal.', 'error')
    
    # Preserve current URL parameters and redirect back
    return redirect(request.referrer or url_for('index'))

@app.route("/refresh", methods=['POST'])
def refresh_data_redirect():
    """Refresh data and redirect back to main page with preserved filters"""
    try:
        data_manager.refresh_data_if_needed()
        flash('Data refreshed successfully!', 'success')
    except Exception as e:
        flash(f'Failed to refresh data: {str(e)}', 'error')
    
    # Preserve current URL parameters and redirect back
    return redirect(request.referrer or url_for('index'))

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

@app.route('/api/filters', methods=['GET', 'POST'])
def manage_filters():
    filters_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs', 'filters.json')
    if request.method == 'GET':
        try:
            print(f"[GET /api/filters] Loading filters from: {filters_path}")
            with open(filters_path, 'r') as f:
                filters = json.load(f)
            print("[GET /api/filters] Loaded filters:")
            print(json.dumps(filters, indent=2))
            return jsonify(filters)
        except FileNotFoundError:
            print(f"[GET /api/filters] Filters file not found at: {filters_path}")
            return jsonify({"error": "Filters file not found."}), 404
        except json.JSONDecodeError as e:
            print(f"[GET /api/filters] Error decoding filters file: {e}")
            return jsonify({"error": "Error decoding filters file."}), 500

    if request.method == 'POST':
        try:
            new_filters = request.json
            print("[POST /api/filters] Saving filters to JSON at:", filters_path)
            print(json.dumps(new_filters, indent=2))
            with open(filters_path, 'w') as f:
                json.dump(new_filters, f, indent=4)
            # After saving filters, start the scraping process (no flags)
            try:
                command = [sys.executable, 'data_retrieval.py', '--notify-app']
                cwd_path = os.path.dirname(os.path.abspath(__file__))
                print(f"[POST /api/filters] Starting scraping process: {' '.join(command)} (cwd={cwd_path})")
                subprocess.Popen(command, cwd=cwd_path)
                return jsonify({"success": True, "message": "Filters saved successfully. Scraping process started."})
            except Exception as e:
                print(f"[POST /api/filters] Filters saved but failed to start scraping: {e}")
                return jsonify({"success": False, "error": f"Filters saved but failed to start scraping: {str(e)}"}), 500
        except Exception as e:
            print(f"[POST /api/filters] Error saving filters: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/api_key', methods=['GET', 'POST'])
def manage_api_key():
    api_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs', 'api_key.json')
    
    if request.method == 'GET':
        try:
            with open(api_key_path, 'r') as f:
                api_key_data = json.load(f)
            return jsonify(api_key_data)
        except FileNotFoundError:
            return jsonify({"error": "API key file not found."}), 404
        except json.JSONDecodeError:
            return jsonify({"error": "Error decoding API key file."}), 500
    
    if request.method == 'POST':
        try:
            new_api_key_data = request.json
            if not isinstance(new_api_key_data, dict):
                return jsonify({"success": False, "error": "Invalid JSON body."}), 400

            print(f"[POST /api/api_key] Saving API key to: {api_key_path}")

            config_data = {}
            if os.path.exists(api_key_path):
                try:
                    with open(api_key_path, 'r') as f:
                        config_data = json.load(f)
                except json.JSONDecodeError:
                    pass # File is empty/corrupt, will be overwritten

            # Update Gemini key if provided
            if 'gemini_api_key' in new_api_key_data:
                config_data['gemini_api_key'] = new_api_key_data['gemini_api_key']
            else:
                return jsonify({"success": False, "error": "'gemini_api_key' not in request."}), 400

            with open(api_key_path, 'w') as f:
                json.dump(config_data, f, indent=4)

            return jsonify({"success": True, "message": "API key saved successfully."})
        except Exception as e:
            print(f"[POST /api/api_key] Error saving API key: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/api_key/perplexity', methods=['POST'])
def manage_perplexity_api_key():
    api_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs', 'api_key.json')
    try:
        body = request.json
        if not isinstance(body, dict) or 'perplexity_api_key' not in body:
            return jsonify({"success": False, "error": "'perplexity_api_key' not in request."}), 400

        print(f"[POST /api/api_key/perplexity] Saving API key to: {api_key_path}")

        config_data = {}
        if os.path.exists(api_key_path):
            try:
                with open(api_key_path, 'r') as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                pass

        config_data['perplexity_api_key'] = body['perplexity_api_key']

        with open(api_key_path, 'w') as f:
            json.dump(config_data, f, indent=4)

        return jsonify({"success": True, "message": "Perplexity API key saved successfully."})
    except Exception as e:
        print(f"[POST /api/api_key/perplexity] Error saving API key: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/login/profellow', methods=['GET', 'POST'])
def manage_profellow_login():
    login_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs', 'login.json')
    
    if request.method == 'GET':
        try:
            with open(login_path, 'r') as f:
                login_data = json.load(f)
            profellow_creds = login_data.get('profellow', {})
            return jsonify(profellow_creds)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({})

    if request.method == 'POST':
        try:
            data = request.json
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return jsonify({"success": False, "error": "Email and password are required."}), 400

            login_data = {}
            if os.path.exists(login_path):
                try:
                    with open(login_path, 'r') as f:
                        login_data = json.load(f)
                except json.JSONDecodeError:
                    pass # file is corrupt or empty

            login_data['profellow'] = {
                "username-email": email,
                "password": password
            }

            with open(login_path, 'w') as f:
                json.dump(login_data, f, indent=4)
            
            return jsonify({"success": True, "message": "Saved Login for Profellow"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if request.method == 'GET':
        # Load filters before rendering the template so values are pre-populated
        filters_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs', 'filters.json')
        filters = {}
        try:
            print(f"[GET /scrape] Loading filters from: {filters_path}")
            with open(filters_path, 'r') as f:
                filters = json.load(f)
            browsing = filters.get('Browsing')
            categories = list(filters.get('categories', {}).keys())
            keywords = filters.get('keywords', {})
            sys_instr_len = len(filters.get('system_instructions', '') or '')
            print(f"[GET /scrape] Loaded. Browsing={browsing}; Categories={categories}; KeywordType={keywords.get('type')}; KeywordCount={len(keywords.get('words', []))}; SystemInstructionsLength={sys_instr_len}")
        except FileNotFoundError:
            print(f"[GET /scrape] Filters file not found at: {filters_path}. Proceeding with defaults.")
        except json.JSONDecodeError as e:
            print(f"[GET /scrape] Error decoding filters file: {e}. Proceeding with defaults.")
        
        # Load API keys if they exist (Gemini and Perplexity)
        api_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs', 'api_key.json')
        api_keys = {}
        try:
            with open(api_key_path, 'r') as f:
                api_key_data = json.load(f)
                api_keys = {
                    'gemini_api_key': api_key_data.get('gemini_api_key', ''),
                    'perplexity_api_key': api_key_data.get('perplexity_api_key', '')
                }
            print(f"[GET /scrape] Loaded API keys (Gemini length: {len(api_keys['gemini_api_key']) if api_keys.get('gemini_api_key') else 0}, Perplexity length: {len(api_keys['perplexity_api_key']) if api_keys.get('perplexity_api_key') else 0})")
        except FileNotFoundError:
            print(f"[GET /scrape] API key file not found at: {api_key_path}")
        except json.JSONDecodeError as e:
            print(f"[GET /scrape] Error decoding API key file: {e}")

        return render_template('scrape.html', filters=filters, api_keys=api_keys)
    
    data = request.get_json()
    cleanup = data.get('cleanup', False)

    command = [sys.executable, 'data_retrieval.py']
    if cleanup:
        command.append('--cleanup')

    try:
        subprocess.Popen(command, cwd=os.path.dirname(os.path.abspath(__file__)))
        return jsonify({'success': True, 'message': 'Scraping process started.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process():
    command = [sys.executable, 'data_retrieval.py', '--refine']
    try:
        subprocess.Popen(command, cwd=os.path.dirname(os.path.abspath(__file__)))
        return jsonify({'success': True, 'message': 'Processing started.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
