import os
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLANNED_DIR = os.path.join(BASE_DIR, 'planned_workouts')
TRACKED_DIR = os.path.join(BASE_DIR, 'finished_workouts')
API_DIR = os.path.join(BASE_DIR, 'api') 

os.makedirs(PLANNED_DIR, exist_ok=True)
os.makedirs(TRACKED_DIR, exist_ok=True)
os.makedirs(API_DIR, exist_ok=True)

def analyze_workout_data():
    all_files = [os.path.join(TRACKED_DIR, f) for f in os.listdir(TRACKED_DIR) if f.endswith('.csv')]
    if not all_files: return {}
    all_files.sort()
    df_list = []
    for i, file_path in enumerate(all_files):
        try:
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            user, workout_name, date = parts[0], parts[1], parts[2]
            df = pd.read_csv(file_path)
            
            # --- NEW: Safely handle columns that might not exist in older files ---
            if 'Actual Reps' not in df.columns: df['Actual Reps'] = 0
            if 'Actual Weight (kg)' not in df.columns: df['Actual Weight (kg)'] = 0
            if 'Target Weight (kg)' not in df.columns: df['Target Weight (kg)'] = 0 # Added for safety
            
            df['workout_number'] = i + 1
            df['date'] = pd.to_datetime(date)
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
    for exercise in agg_df['Exercise'].unique():
        exercise_df = agg_df[agg_df['Exercise'] == exercise].sort_values('workout_number')
        analysis_results[exercise] = {
            'labels': exercise_df['workout_number'].tolist(),
            'dates': exercise_df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'users': exercise_df['user'].tolist(),
            'max_weight': exercise_df['max_weight'].tolist(),
            'total_volume': exercise_df['total_volume'].tolist()
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

@app.route('/api/list_all_workouts', methods=['GET'])
def list_all_workouts():
    try:
        planned_files = [{'filename': f, 'type': 'plan'} for f in os.listdir(PLANNED_DIR) if f.endswith('.csv')]
        tracked_files = [{'filename': f, 'type': 'tracked'} for f in os.listdir(TRACKED_DIR) if f.endswith('.csv')]
        all_workouts = planned_files + tracked_files
        all_workouts.sort(key=lambda x: x['filename'], reverse=True)
        return jsonify({"status": "success", "workouts": all_workouts}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Could not list workouts."}), 500

@app.route('/api/get_workout', methods=['GET'])
def get_workout_file():
    filename = request.args.get('filename')
    workout_type = request.args.get('type')
    if not filename or not workout_type:
        return jsonify({"status": "error", "message": "Filename and type are required."}), 400
    directory = PLANNED_DIR if workout_type == 'plan' else TRACKED_DIR
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

@app.route('/api/list_plans', methods=['GET'])
def list_plans():
    try:
        files = [f for f in os.listdir(PLANNED_DIR) if f.endswith('.csv')]
        files.sort(reverse=True) 
        return jsonify({"status": "success", "plans": files}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Could not list workout plans."}), 500

@app.route('/api/get_plan/<path:filename>')
def get_plan(filename):
    try:
        return send_from_directory(PLANNED_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found."}), 404

@app.route('/api/save_workout', methods=['POST'])
def save_workout():
    try:
        data = request.get_json()
        filename, csv_content, workout_type = data.get('filename'), data.get('csv_content'), data.get('type')
        if not all([filename, csv_content, workout_type]):
            return jsonify({"status": "error", "message": "Missing filename, content, or type"}), 400
        save_dir = PLANNED_DIR if workout_type == 'plan' else TRACKED_DIR
        if '..' in filename or '/' in filename:
             return jsonify({"status": "error", "message": "Invalid filename"}), 400
        with open(os.path.join(save_dir, filename), 'w') as f:
            f.write(csv_content)
        return jsonify({"status": "success", "message": f"Workout '{filename}' saved."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
