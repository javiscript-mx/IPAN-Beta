from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

from searchEngine import KeywordIdentifier, PatentScopeScraper, ResultsHandler
from dataHandler import Seeker, Analyzer, Scrubber, Manager
from dataProcessor import PatentSearchAI, PatentSearchWithNearestNeighbors
app = Flask(__name__)
#CORS(app, resources={r"/api/*": {"origins": "http://localhost"}})
CORS(app)
print(app.config)

#DataHandler
seeker = Seeker()

@app.route('/api/test', methods=['GET'])
def test():
   print("SUCCEED TEST")
   return jsonify({"message":"API funcionando..."}), 200

@app.route('/api/buscar_patentes', methods=['POST'])
def buscar_patentes():
    # Instancia de las clases y variables
    username = '.'
    password = '.'
    #SearchEngine
    results_handler = ResultsHandler()
    data = request.get_json()
    message = 'La búsqueda de patentes se ha realizado exitosamente'
    result = {}

    if 'query' not in data:
        return jsonify({'error': 'El campo "query" es obligatorio'}), 400

    query = data['query']

     #Validacion de datos existentes para optimizar el proceso
    print("Validando si existen datos para esa consulta...")
    existing_data = results_handler.validate_existing_query(query)
    #Si no existen datos relacionados con esa busqueda
    if existing_data == False:
      patent_scope_scraper = PatentScopeScraper(username, password)
      #Obtener datos
      #print("Obteniendo datos de patent scope...")
      if patent_scope_scraper.login():
         #print("Autentificacion exitosa...")
         patent_scope_scraper.search_and_download(query)
         #print("Datos descargados exitosamente...")
         patent_scope_scraper.close()
         #print("Procesando datos...")
         existing_data = results_handler.parse_and_save_data(query)
      else:
         print("No pudimos obtener datos para esa búsqueda...")
    #else:
       #Si ya existian datos buscamos en el analizador
        #print("Tenemos datos")
    
    if existing_data == False:
      message = 'No pudimos encontrar datos para esta consulta.'
    else:
      result['Query'] = existing_data["Query"]
      result['totalRecords'] = len(existing_data["Data"])

    return jsonify({'message': message,"results":result}), 200

@app.route('/api/analizar_patentes', methods=['POST'])
def analizar_patentes():
    data = request.get_json()
    message = 'El análisis de patentes se ha realizado exitosamente'
    if 'query' not in data:
        return jsonify({'error': 'El campo "query" es obligatorio'}), 400
    else:
        query = data['query']
    
    try:
        result = {}
        print("Obteniendo registros...")
        existing_data, filename = seeker.get_records(query)
        #print(existing_data)
        if existing_data:
            #print("Obteniendo estadísticas...")
            analyzer = Analyzer(existing_data['Data'],"Remote")
            
            # Realizar el análisis estadístico
            numeric_stats, unique_countries, total_applications, total_publications, patents_per_country = analyzer.compute_statistics()
            analisisFechasSolicitud,analisisFechasPublicacion = analyzer.analyze_dates()
            # Construir el resultado
            result["patentesPorPais"] = analyzer.count_patents_by_country()
            result["palabrasClaveTitulos"] = analyzer.analyze_title_and_abstract()[0]
            result["palabrasClaveResumen"] = analyzer.analyze_title_and_abstract()[1]
            result["analisisFechasSolicitud"] = analisisFechasSolicitud
            result["analisisFechasPublicacion"] = analisisFechasPublicacion
            #result["estadisticasNumericas"] = numeric_stats
            result["paisesUnicos"] = unique_countries
            result["totalAplicaciones"] = total_applications
            result["totalPublicaciones"] = total_publications
            return jsonify(result), 200
        else:
            return jsonify({'error': 'No se encontraron registros para la consulta especificada'}), 404
    except Exception as e:
        return jsonify({'error': f'Error durante el análisis de patentes: {str(e)}'}), 500

@app.route('/api/procesar_patentes', methods=['POST'])
def procesar_patentes():
    data = request.get_json()
    message = 'La búsqueda de patentes se ha realizado exitosamente'
    result = {}

    if 'query' not in data:
        return jsonify({'error': 'El campo "query" es obligatorio'}), 400
    else:
      query = data['query']
    try:
      result = {}
      #print("Obteniendo registros...")
      existing_data, filename = seeker.get_records(query)
      if existing_data:
          print("Procesando resultado con IA...")
      search_ai = PatentSearchAI(existing_data)
      related_patents = search_ai.find_most_related_patents(query)
      return jsonify({'message': message,"results":related_patents}), 200
    except Exception as e:
      return jsonify({'error': f'Error durante el análisis de patentes: {str(e)}'}), 500

@app.route('/api/procesar_patentes2', methods=['POST'])
def procesar_patentes2():
    data = request.get_json()
    message = 'La búsqueda de patentes se ha realizado exitosamente'
    result = {}

    if 'query' not in data:
        return jsonify({'error': 'El campo "query" es obligatorio'}), 400

    query = data['query']
    #try:
    result = {}
    #print("Obteniendo registros...")
    existing_data, filename = seeker.get_records(query)
    #if existing_data:
        #print("Procesando resultado con IA...")
    search_ai = PatentSearchWithNearestNeighbors(existing_data)
    related_patents = search_ai.find_most_related_patents(query)
    return jsonify({'message': message,"results":related_patents}), 200
    #except Exception as e:
    #  return jsonify({'error': f'Error durante el análisis de patentes: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
    app.run(debug=True)
