import os
import mercadopago # type: ignore
from flask import Flask, render_template, request, jsonify # type: ignore

app = Flask(__name__)

# --- TUS CREDENCIALES ---
TOKEN = "APP_USR-7248952077909583-031821-2618d41cc5257eb434bed2af07f8e0f2-3275075253"
sdk = mercadopago.SDK(TOKEN)

usuarios_pagados = {} 

def calcular_protocolo_completo(peso, altura, edad, actividad, objetivo):
    tmb = (10 * peso) + (6.25 * altura) - (5 * edad) + 5
    mantenimiento = tmb * actividad
    
    if objetivo == "definicion":
        calorias = mantenimiento - 450
        p_rango, c_rango = (2.2, 2.6), (2.0, 3.0)
    elif objetivo == "volumen":
        calorias = mantenimiento + 400
        p_rango, c_rango = (1.8, 2.2), (4.0, 6.0)
    else: # Mantenimiento
        calorias = mantenimiento
        p_rango, c_rango = (1.6, 2.0), (3.0, 4.0)
    
    return {
        "calorias": round(calorias),
        "prot_min": round(peso * p_rango[0]),
        "prot_max": round(peso * p_rango[1]),
        "carb_min": round(peso * c_rango[0]),
        "carb_max": round(peso * c_rango[1]),
        "grasas": round(peso * 0.9),
        "grasa_sat_max": 20, # RECUPERADO
        "azucar_max": 25,
        "sal_max": 5,
        "objetivo": objetivo.upper()
    }

from flask import Flask, render_template # Asegurate de tener render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('calculadora.html')

@app.route('/crear_preferencia', methods=['POST'])
def crear_preferencia():
    data = request.get_json()
    # PREFERENCIA ULTRA SIMPLE
    preference_data = {
        "items": [
            {
                "title": "SERVICIO ELITE",
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": 1000
            }
        ],
        "payer": {
            "email": "test_user_123@testuser.com" # Usamos uno genérico para probar
        }
    }
    try:
        res = sdk.preference().create(preference_data)
        return jsonify(res["response"])
    except Exception as e:
        print(f"ERROR REAL: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/confirmar_pago_manual', methods=['POST'])
def confirmar_pago_manual():
    data = request.get_json()
    usuarios_pagados[data.get('email', '').strip().lower()] = True 
    return jsonify({"status": "OK"})


@app.route('/obtener_resultados', methods=['POST'])
def obtener_resultados():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    # LOG PARA DEPURAR
    print(f"Intentando obtener resultados para: {email}")
    print(f"Lista de usuarios que pagaron: {usuarios_pagados}")

    # Verificamos si el usuario pagó
    if not usuarios_pagados.get(email):
        print("ERROR: El email no figura como pagado.")
        return jsonify({"error": "Pago no verificado"}), 403

    try:
        # Aquí va tu lógica de cálculo de macros
        # Asegúrate de que estas variables existan y sean números
        peso = float(data.get('peso', 0))
        altura = float(data.get('altura', 0))
        edad = int(data.get('edad', 0))
        
        # Ejemplo de respuesta (ajustalo a tus fórmulas)
        res = {
            "objetivo": data.get('objetivo', '').upper(),
            "calorias": 2500,  # Pon aquí tu fórmula
            "prot_min": 150, "prot_max": 180,
            "carb_min": 200, "carb_max": 250,
            "grasas": 70,
            "grasa_sat_max": 20, "azucar_max": 25, "sal_max": 5
        }
        return jsonify(res)
    except Exception as e:
        print(f"ERROR EN CÁLCULO: {str(e)}")
        return jsonify({"error": "Error en el cálculo de datos"}), 500
    
    res = calcular_protocolo_completo(float(data['peso']), float(data['altura']), int(data['edad']), float(data['actividad']), data['objetivo'])
    return jsonify(res)

if __name__ == '__main__':
    # Esto permite que el celular entre por el Wi-Fi
    app.run(host='0.0.0.0', port=5001, debug=True)
