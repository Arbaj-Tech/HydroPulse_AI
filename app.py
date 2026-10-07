from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# 1. DATABASE FETCH FUNCTION (WITH ACTIVE AUTOCOMMIT TO FORCE REFRESH)
def get_db_data():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="hydropulse_db"
    )
    cursor = db.cursor(dictionary=True)
    
    # Live fresh pull straight from SQL tables
    cursor.execute("SELECT * FROM kolkata_drainage_grid")
    zones = cursor.fetchall()
    
    # SHORTEST ROUTE LOGISTICS ALGORITHM
    critical_zones = [z for z in zones if z["water_level_cm"] >= 30]
    optimized_route = sorted(critical_zones, key=lambda x: x["distance_km"])
    
    cursor.close()
    db.close()
    return zones, optimized_route

# ROUTE 1: RENDER THE LIVE DASHBOARD
@app.route('/')
def dashboard():
    all_zones, best_route = get_db_data()
    return render_template('index.html', zones=all_zones, route=best_route)

# ROUTE 2: SAVE PUBLIC COMPLAINTS TO DATABASE AND FORCE COMMIT
@app.route('/report', methods=['POST'])
def report_incident():
    citizen_name = request.form.get('username')
    selected_zone = request.form.get('zone')
    severity = request.form.get('severity')
    
    water_impact = 20
    if severity == "medium": water_impact = 45
    elif severity == "high": water_impact = 65

    db = mysql.connector.connect(
        host="localhost", user="root", password="", database="hydropulse_db"
    )
    cursor = db.cursor()
    
    # SQL Update Query: Injects public inputs into database rows instantly
    query = "UPDATE kolkata_drainage_grid SET water_level_cm = %s, silt_blockage_pct = LEAST(silt_blockage_pct + 10, 100) WHERE zone_name = %s"
    cursor.execute(query, (water_impact, selected_zone))
    
    # Force save changes into database matrix immediately
    db.commit()
    
    cursor.close()
    db.close()
    
    # Instant redirection back to homepage to reload components
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5000)