import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime

import nltk
from nltk.corpus import wordnet
from collections import Counter


class KeywordIdentifier:
    def __init__(self):
        pass

    def get_keywords(self, query):
        # Descarga recursos necesarios de NLTK
        # nltk.download('punkt')
        # nltk.download('wordnet')
        # nltk.download('averaged_perceptron_tagger')
        # nltk.download('omw-1.4')

        # Tokenización de la consulta
        tokens = nltk.word_tokenize(query)
        
        # Extracción de sustantivos y adjetivos
        tags = nltk.pos_tag(tokens)
        keywords = [word for word, tag in tags if tag.startswith('NN') or tag.startswith('JJ')]
        
        return keywords

    def generate_synonyms(self, word):
        synonyms = []
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonyms.append(lemma.name())
        return synonyms

    def suggest_keywords(self, query):
        keywords = self.get_keywords(query)
        suggested_keywords = []

        for keyword in keywords:
            # Agregar la palabra clave original
            suggested_keywords.append(keyword)

            # Generar sinónimos
            synonyms = self.generate_synonyms(keyword)
            suggested_keywords.extend(synonyms)

        # Contar la frecuencia de cada palabra clave sugerida
        keyword_counter = Counter(suggested_keywords)

        # Ordenar las palabras clave sugeridas por frecuencia
        suggested_keywords_sorted = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)

        return suggested_keywords_sorted

class PatentScopeScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome()

    def login(self):
        try:
            self.driver.get("https://www3.wipo.int/authpage/signin.xhtml?goto=https%3A%2F%2Fwww3.wipo.int%3A443%2Fam%2Foauth2%2Fauthorize%3Fclient_id%3Dpatentscope1Prd%26redirect_uri%3Dhttps%253A%252F%252Fpatentscope.wipo.int%252Fsearch%252Fwiposso%252Floggedin%26response_type%3Dcode%26scope%3Dopenid%2Bprofile%2Bemail%26state%3DXG6Su17zdJrq87JzgfjWoAGoLgvbu3v2PLEE8_N_S7M")

            # Find and fill in the username field
            username_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#authform_fields\\:0\\:authform_text\\:input'))
            )
            username_field.send_keys(self.username)

            # Find and fill in the password field
            password_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#authform_fields\\:1\\:authform_mask\\:input'))
            )
            password_field.send_keys(self.password)

            # Submit the login form
            password_field.send_keys(Keys.RETURN)

            # Optionally, you can wait for any other elements on the PatentScope search page that indicate successful login

        except Exception as e:
            print("Error during login:", e)
            self.driver.quit()
            return False
        return True

    def search_and_download(self, query):
        try:
            # Navigate to the PatentScope search page
            self.driver.get('https://patentscope.wipo.int/search/en/search.jsf')

            # Wait for the search input field to be visible
            search_input = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '#simpleSearchForm\\:fpSearch\\:input'))
            )

            # Input the query into the search field
            search_input.send_keys(query)

            # Submit the search form
            search_input.send_keys(Keys.RETURN)

            # Wait for the search results to load
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, 'resultListCommandsForm'))
            )

            # Find and click the download button for XLS file
            download_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'resultListCommandsForm:triggerDownloadMenu'))
            )
            download_button.click()
            xls_sub_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="resultListCommandsForm:downloadMenu"]/ul/li[2]'))
            )
            xls_sub_option.click()
            # Give some time for the file to download
            time.sleep(25)  # Adjust the time as needed based on the file size and download speed

        except Exception as e:
            print('Error:', e)

    def close(self):
        self.driver.quit()

class ResultsHandler:
    def __init__(self, environment="Remote"):
      self.environment = environment
      self.script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def validate_existing_query(self, query):
      query = query.lower().replace(" ","")
      result = False
      if self.environment == "Local":
        directory = self.script_dir+"/backend/local_storage"
        # Iterate over files in the directory
        for filename in os.listdir(directory):
          filepath = os.path.join(directory, filename)
          print("Query: "+query+" - filename: "+filename)
          if query == filename.split("_")[0]:
            print("Se encontraron resultados precargados para consulta: "+query)
            # Reas JSON
            with open(filepath, "r") as archivo:
              result = json.load(archivo)
      else:
        # List all files in the bucket
        bucket = self.connect_to_firebase('storage')
        blobs = bucket.list_blobs()
        # Iterate over each file in the bucket
        for blob in blobs:
          # Check if the file name contains the sentence
          filename = blob.name
          if query == filename.split("_")[0]:
            print("Se encontraron resultados precargados para consulta: "+query)
            # Download the file's content as a string
            file_content = blob.download_as_string().decode("utf-8")
            # Parse the string as JSON
            json_data = json.loads(file_content)
            result = json_data  # Return the JSON data
            
      return result

    def parse_and_save_data(self, query):
        query = query.lower().replace(" ","")
        # Obtener la fecha y hora actual
        fecha_actual = datetime.now()
        # Formatear la fecha y hora en el formato YYYYMMDDHHSS
        cadena_fecha = fecha_actual.strftime("%Y%m%d%H%M%S")
        # Define the directory where the files are located
        directory = os.path.expanduser('~/Downloads/')

        # Get a list of all files in the directory
        files = os.listdir(directory)

        # Filter files that start with 'resultList' and end with '.xls'
        filtered_files = [file for file in files if file.startswith('resultList') and file.endswith('.xls')]

        # Sort the filtered files by modification time
        sorted_files = sorted(filtered_files, key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
        print(sorted_files)
        # Check if there are any matching files
        if sorted_files:
            # Get the path of the last saved file
            last_saved_file = os.path.join(directory, sorted_files[0])
            print("Last saved file:", last_saved_file)
        else:
            print("No matching files found.")
            return
        # Read downloaded excel file and convert it to JSON
        excel_file_path = last_saved_file#os.path.expanduser('~/Downloads/resultList.xls')
        df = pd.read_excel(excel_file_path)
        # Obtener los datos del encabezado (Time, Query, SortBy)
        encabezado = df.iloc[0:3, 0:2].set_index("Unnamed: 0").to_dict()["Unnamed: 1"]
        # Obtener los nombres de las columnas
        nombres_columnas = df.iloc[4].tolist()
        # Obtener los datos de las filas restantes
        datos_filas = df.iloc[5:]
        datos_filas.columns = nombres_columnas
        dataResults = datos_filas.reset_index(drop=True).to_dict(orient='records')
        # Construimos el json a guardar
        json_resultado = {
          "Time": encabezado["Time:"],
          "Query": encabezado["Query:"],
          "SortBy": encabezado["SortBy:"],
          "Data": dataResults
        }
        # Convert the JSON object to a string
        json_str = json.dumps(json_resultado)
        # Define el nombre del archivo en el bucket (puedes usar cualquier nombre)
        filename = f"{query.replace(' ', '')}_{cadena_fecha}.json"
        if self.environment == "Local":
          ruta_archivo = os.path.join(self.script_dir, "backend/local_storage/"+filename)
          # Guardar la cadena JSON en el archivo
          with open(ruta_archivo, "w") as archivo:
              archivo.write(json_str)
        else:
          # Get the size of the string in bytes
          size_bytes = len(json_str.encode())
          print("Guardando en Cloud Storage " + str(size_bytes) + " bytes de datos")
          # Obtener una referencia al bucket de Cloud Storage
          bucket = self.connect_to_firebase('storage')
          # Subir un archivo al bucket
          blob = bucket.blob(filename)
          blob.upload_from_string(json_str)
        # Verificar si el archivo existe antes de intentar borrarlo
        if os.path.exists(last_saved_file):
            # Borrar el archivo
            os.remove(last_saved_file)
        return json_resultado          

    def connect_to_firebase(self,service):
      if not firebase_admin._apps:
        # Path to Firebase credentials file
        credentials_path = os.path.join("./", "firebase-credentials.json")
        cred = credentials.Certificate(credentials_path)
        # Initialize Firebase Admin SDK with a unique app name
        firebase_admin.initialize_app(cred, {'projectId': 'ipan-413419'})
      if service == "firestore":
        db = firestore.client()
        return db
      elif service == "storage":
        return storage.bucket("ipan-413419.appspot.com")
