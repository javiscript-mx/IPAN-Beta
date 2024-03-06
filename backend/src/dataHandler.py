import os
import re
import json
import matplotlib.pyplot as plt #Libreria para graficar
import seaborn as sns 
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from collections import defaultdict


# Preprocesamiento de datos: Antes de aplicar técnicas de inteligencia artificial,
# es importante preprocesar los datos para limpiarlos, normalizarlos y prepararlos
# para el análisis. Esto puede incluir la eliminación de datos duplicados, el manejo
# de valores faltantes, la normalización de datos numéricos y la codificación de 
# datos categóricos.
class PatentData:
    def __init__(self, data):
        self.application_id = data.get("Application Id")
        self.application_number = data.get("Application Number")
        self.application_date = data.get("Application Date")
        self.publication_number = data.get("Publication Number")
        self.publication_date = data.get("Publication Date")
        self.country = data.get("Country")
        self.title = data.get("Title")
        self.abstract = data.get("Abstract")
        self.ipc = data.get("I P C")
        self.applicants = data.get("Applicants")
        self.inventors = data.get("Inventors")
        self.priorities_data = data.get("Priorities Data")
        self.national_phase_entries = data.get("National Phase Entries")
        self.image = data.get("Image")

class Analyzer:
  def __init__(self, dataset, environment="Local"):
    self.dataset = dataset
    self.environment = environment
    self.script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

  def count_patents_by_country(self):
    # Implementar el conteo de patentes por país
    patent_counts = {}
    for data in self.dataset:
        country = data.get("Country")
        if country in patent_counts:
            patent_counts[country] += 1
        else:
            patent_counts[country] = 1
    return patent_counts

  def extract_keywords(self, text):
        # Tokenizar el texto
        tokens = word_tokenize(text)
        
        # Eliminar las stopwords
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [word for word in tokens if word.lower() not in stop_words]
        
        # Lematizar las palabras
        lemmatizer = WordNetLemmatizer()
        lemmatized_tokens = [lemmatizer.lemmatize(word) for word in filtered_tokens]      
        return lemmatized_tokens
  
  def analyze_title_and_abstract(self):
        # Implementar la extracción de palabras clave del título y el resumen
        title_keywords = {}
        abstract_keywords = {}

        for data in self.dataset:
            title = data.get("Title")
            abstract = data.get("Abstract")
            abstract_tokens = []
            title_tokens = []
            #print(data.get("Abstract"))
            #print(data.get("Title"))
            if title != None and title != "":
              if not isinstance(title, float):
                title = str(title.lower())
                clean_title = re.sub(r'[^\w\s]', '', title)
                title_tokens = self.extract_keywords(clean_title)
            if abstract != None and abstract != "":
                if not isinstance(abstract, float):
                  abstract = str(abstract.lower())
                  clean_abstract = re.sub(r'[^\w\s]', '', abstract)
                  abstract_tokens = self.extract_keywords(clean_abstract)

            for token in title_tokens:
                if token in title_keywords:
                    title_keywords[token] += 1
                else:
                    title_keywords[token] = 1

            for token in abstract_tokens:
                if token in abstract_keywords:
                    abstract_keywords[token] += 1
                else:
                    abstract_keywords[token] = 1

        return title_keywords, abstract_keywords

  def analyze_dates(self):
        # Implementar el análisis de fechas de solicitud y publicación
        application_dates = defaultdict(int)
        publication_dates = defaultdict(int)

        for data in self.dataset:
            application_date = data.get("Application Date")
            publication_date = data.get("Publication Date")

            # Actualizar el contador para la fecha de solicitud
            if application_date and str(application_date) != "nan":
                application_dates[str(application_date)] += 1

            # Actualizar el contador para la fecha de publicación
            if publication_date and str(publication_date) != "nan":
                publication_dates[str(publication_date)] += 1

        return [application_dates, publication_dates]
  
  def compute_statistics(self):
        # Crear un DataFrame de pandas para facilitar el cálculo de estadísticas
        df = pd.DataFrame(self.dataset)

        # Calcular estadísticas para campos numéricos
        numeric_stats = df.describe(include='all').to_dict()

        # Calcular la cantidad de países únicos
        unique_countries = df['Country'].nunique()

        # Calcular la cantidad de aplicaciones y publicaciones
        total_applications = df['Application Number'].nunique()
        total_publications = df['Publication Number'].nunique()

        # Calcular la cantidad de patentes por país
        patents_per_country = df['Country'].value_counts().to_dict()

        return numeric_stats, unique_countries, total_applications, total_publications, patents_per_country
      
class Scrubber:
  def remove_duplicates(self):
    return False
  
  def dataCleaning(self):
    # Convertir a minúsculas
    text = text.lower()
    
    # Eliminar caracteres especiales
    text = re.sub(r'[^\w\s]', '', text)
    return

class Seeker:
  def __init__(self, environment="Remote"):
    self.environment = environment
    self.script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

  def get_records(self, query):
    query = query.lower().replace(" ","")
    result = False
    if self.environment == "Local":
      directory = self.script_dir+"/backend/local_storage"
      # Iterate over files in the directory
      for filename in os.listdir(directory):
        print(filename.split("_")[0])
        if query == filename.split("_")[0]:
          filepath = os.path.join(directory, filename)
          print("Se encontraron resultados locales precargados para consulta: "+query)
          # Reas JSON
          with open(filepath, "r") as archivo:
            result = json.load(archivo), filename
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
          result = json_data, blob.name  # Return the JSON data
    return result 

  def connect_to_firebase(self,service):
    if not firebase_admin._apps:
      # Path to Firebase credentials file
      credentials_path = os.path.join(self.script_dir, "backend/firebase-credentials.json")
      cred = credentials.Certificate(credentials_path)
      # Initialize Firebase Admin SDK with a unique app name
      firebase_admin.initialize_app(cred, {'projectId': 'ipan-413419'})
    if service == "firestore":
      db = firestore.client()
      return db
    elif service == "storage":
      return storage.bucket("ipan-413419.appspot.com")

class Manager:
  def __init__(self, environment="Local"):
    self.environment = environment
    self.script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

  def remove_duplicates(self):
    return False
  