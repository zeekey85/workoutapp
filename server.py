import os
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import shutil

app = Flask(__name__)
CORS(app)

# --- DIRECTORY SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLANNED_DIR = os.path.join(BASE_DIR, 'planned_workouts')
INPROGRESS_DIR = os.path.join(BASE_DIR, 'inprogress_workouts')
FINISHED_DIR = os.path.join(BASE_DIR, 'finished_workouts')
ARCHIVED_DIR = os.path.join(BASE_DIR, 'archived_plans')
API_DIR = os.path.join(BASE_DIR, 'api')

# Create all necessary directories on startup
os.makedirs(PLANNED_DIR, exist_ok=True)
os.makedirs(INPROGRESS_DIR, exist_ok=True)
os.makedirs(FINISHED_DIR, exist_ok=True)
os.makedirs(ARCHIVED_DIR, exist_ok=True)
os.makedirs(API_DIR, exist_ok=True)

def analyze_workout_data():
    """Analyzes data from the finished_workouts directory."""
    all_files = [os.path.join(FINISHED_DIR, f) for f in os.listdir(FINISHED_DIR) if f.endswith('.csv')]
    if not all_files: return {}
    all_files.sort()
    df_list = []
    for i, file_path in enumerate(all_files):
        try:
            filename = os.path.basename(file_path)
            
            filename_base = filename.replace('_tracked.csv', '')
            parts = filename_base.split('_')
            if len(parts) < 3: continue
            
            user = parts[0]
            date_str = parts[-1]
            
            try:
                pd.to_datetime(date_str)
            except ValueError:
                print(f"Skipping file with invalid date: {filename}")
                continue

            df = pd.read_csv(file_path)
            
            if 'Actual Reps' not in df.columns: df['Actual Reps'] = 0
            if 'Actual Weight (kg)' not in df.columns: df['Actual Weight (kg)'] = 0
            if 'Target Weight (kg)' not in df.columns: df['Target Weight (kg)'] = 0
            
            df['workout_number'] = i + 1
            df['date'] = pd.to_datetime(date_str)
            df['user'] = user
            df_list.append(df)
        except Exception as e:
            print(f"Could not process file {file_path}: {e}")
            continue
            
    if not df_list: return {}
    
    full_df = pd.concat(df_list, ignore_index=True)
    full_df['Actual Reps'] = pd.to_numeric(full_df['Actual Reps'], errors='coerce').fillna(0)
    full_df['Actual Weight (kg)'] = pd.to_numeric(full_df['Actual Weight (kg)'], errors='coerce').fillna(0)
    full_df['volume'] = full_df['Actual Reps'] * full_df['Actual Weight (kg)']
    
    agg_df = full_df.groupby(['Exercise', 'workout_number', 'date', 'user']).agg(
        max_weight=('Actual Weight (kg)', 'max'),
        total_volume=('volume', 'sum')
    ).reset_index()
    
    analysis_results = {}
    for exercise_name, group in agg_df.groupby('Exercise'):
        group = group.sort_values('date')
        analysis_results[exercise_name] = {
            'labels': group['workout_number'].tolist(),
            'dates': group['date'].dt.strftime('%Y-%m-%d').tolist(),
            'users': group['user'].tolist(),
            'max_weight': group['max_weight'].tolist(),
            'total_volume': group['total_volume'].tolist()
        }
    return analysis_results

@app.route('/api/get_exercises', methods=['GET'])
def get_exercises():
    try:
        exercises_path = os.path.join(API_DIR, 'exercises.csv')
        df = pd.read_csv(exercises_path)
        return jsonify({"status": "success", "exercises": df['Exercise'].tolist()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Could not read exercises file."}), 500

@app.route('/api/list_templates', methods=['GET'])
def list_templates():
    try:
        finished_files = [{'filename': f, 'type': 'finished'} for f in os.listdir(FINISHED_DIR) if f.endswith('.csv')]
        archived_files = [{'filename': f, 'type': 'archived'} for f in os.listdir(ARCHIVED_DIR) if f.endswith('.csv')]
        
        all_templates = finished_files + archived_files
        all_templates.sort(key=lambda x: x['filename'], reverse=True)
        return jsonify({"status": "success", "templates": all_templates}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Could not list templates."}), 500

@app.route('/api/list_finished_workouts', methods=['GET'])
def list_finished_workouts():
    """Lists all workouts in the finished_workouts directory."""
    try:
        files = [f for f in os.listdir(FINISHED_DIR) if f.endswith('.csv')]
        files.sort(reverse=True)
        return jsonify({"status": "success", "workouts": files}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Could not list finished workouts."}), 500

@app.route('/api/list_workouts_for_tracker', methods=['GET'])
def list_workouts_for_tracker():
    try:
        planned_files = [f for f in os.listdir(PLANNED_DIR) if f.endswith('.csv')]
        in_progress_files = [f for f in os.listdir(INPROGRESS_DIR) if f.endswith('_tracked.csv')]
        
        plans_in_progress_base = {f.replace('_tracked.csv', '.csv') for f in in_progress_files}
        active_plans = [p for p in planned_files if p not in plans_in_progress_base]

        active_plans.sort(reverse=True)
        in_progress_files.sort(reverse=True)

        return jsonify({
            "status": "success", 
            "plans": active_plans,
            "tracked": in_progress_files
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Could not list workouts."}), 500

@app.route('/api/get_workout', methods=['GET'])
def get_workout_file():
    filename = request.args.get('filename')
    workout_type = request.args.get('type')
    if not filename or not workout_type:
        return jsonify({"status": "error", "message": "Filename and type are required."}), 400
    
    dir_map = {
        'plan': PLANNED_DIR,
        'tracked': INPROGRESS_DIR,
        'finished': FINISHED_DIR,
        'archived': ARCHIVED_DIR
    }
    directory = dir_map.get(workout_type)

    if not directory:
        return jsonify({"status": "error", "message": "Invalid workout type."}), 400
    
    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found."}), 404

@app.route('/api/get_analysis', methods=['GET'])
def get_analysis():
    try:
        results = analyze_workout_data()
        return jsonify({"status": "success", "analysis": results}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Could not perform analysis."}), 500

@app.route('/api/save_workout', methods=['POST'])
def save_workout():
    try:
        data = request.get_json()
        filename, csv_content, workout_type = data.get('filename'), data.get('csv_content'), data.get('type')
        if not all([filename, csv_content, workout_type]):
            return jsonify({"status": "error", "message": "Missing filename, content, or type"}), 400
        
        if workout_type == 'plan':
            save_dir = PLANNED_DIR
        elif workout_type == 'tracked':
            save_dir = INPROGRESS_DIR
        else:
            return jsonify({"status": "error", "message": "Invalid workout type for saving."}), 400
        
        if '..' in filename or '/' in filename:
             return jsonify({"status": "error", "message": "Invalid filename"}), 400
        
        with open(os.path.join(save_dir, filename), 'w', newline='', encoding='utf-8') as f:
            f.write(csv_content)
        
        return jsonify({"status": "success", "message": f"Workout '{filename}' saved."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/complete_workout', methods=['POST'])
def complete_workout():
    try:
        data = request.get_json()
        tracked_filename = data.get('tracked_filename')
        plan_filename = data.get('plan_filename')

        if not tracked_filename or not plan_filename:
            return jsonify({"status": "error", "message": "Tracked and plan filenames are required."}), 400

        inprogress_path = os.path.join(INPROGRESS_DIR, tracked_filename)
        finished_path = os.path.join(FINISHED_DIR, tracked_filename)
        plan_path = os.path.join(PLANNED_DIR, plan_filename)
        archive_path = os.path.join(ARCHIVED_DIR, plan_filename)

        if os.path.exists(inprogress_path):
            shutil.move(inprogress_path, finished_path)
        
        if os.path.exists(plan_path):
            shutil.move(plan_path, archive_path)
        else:
            print(f"Warning: Plan file '{plan_filename}' not found for archiving, but completing workout.")

        return jsonify({"status": "success", "message": "Workout completed and archived."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
