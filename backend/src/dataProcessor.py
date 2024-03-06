import tensorflow as tf
import tensorflow_hub as hub
from dataHandler import Seeker
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

class PatentSearchAI:
    def __init__(self, json_data):
        self.patents = []
        self.load_data(json_data)
        self.model = self.load_use_model()

    def load_data(self, json_data):
        for entry in json_data['Data']:
            self.patents.append(entry)

    def load_use_model(self):
      return hub.load("modelUSE/")

    def find_most_related_patents(self, query, num_patents=20):
      if isinstance(query, str):
        query = [query]
      query_embedding = self.model(query)
      related_patents = []
      print("Procesando patentes...")
      for patent in self.patents:
        similarity_abstract = 0
        similarity_title = 0
        #if patent["Abstract"] != None and patent["Abstract"] != None:
        if not isinstance(patent["Abstract"], float) and  not isinstance(patent["Title"], float):
           # Combina el título y el resumen de la patente
            text = patent['Title'] + " " + patent['Abstract']
            # Obtiene la incrustación para el texto combinado
            text_embedding = self.model([text])[0]
            # Calcula la similitud entre la incrustación de la consulta y la incrustación de la patente
            similarity = tf.keras.losses.cosine_similarity(query_embedding, text_embedding).numpy()[0]
            #patent_embedding_abstract = self.model([patent['Abstract']])[0]
            #similarity_abstract = tf.keras.losses.cosine_similarity(query_embedding, patent_embedding_abstract).numpy()[0]
        #if patent["Title"] != None and patent["Title"] != None: 
        #  if not isinstance(patent["Title"], float):
        #    patent_embedding_title = self.model([patent['Title']])[0]
        #    similarity_title = tf.keras.losses.cosine_similarity(query_embedding, patent_embedding_title).numpy()[0]
        #similarity = similarity_abstract + similarity_title
        related_patents.append((patent, similarity))
      pre_result= sorted(related_patents, key=lambda x: x[1], reverse=False)[:num_patents]
      result=[]
      for item in pre_result:
         newItem = {}
         newItem["similarity"] = np.float64((item[1])*-1)
         newItem["Title"]=str(item[0]["Title"])
         newItem["Abstract"]=str(item[0]["Abstract"])
         newItem["Country"]=item[0]["Country"]
         newItem["Inventors"]=str(item[0]["Inventors"])
         newItem["PublicationDate"]=item[0]["Publication Date"]
         newItem["TopScore"] = np.float64((pre_result[0][1])*-1)
         result.append(newItem)
      return result
    
class PatentSearchWithNearestNeighbors:
    def __init__(self, json_data):
        self.patents = []
        self.load_data(json_data)
        self.vectorizer = TfidfVectorizer()
        self.X = self.vectorizer.fit_transform([patent['Title'] + " " + patent['Abstract'] for patent in self.patents])
        print(len(json_data["Data"]))
        if len(json_data['Data']) >= 20:
          self.nn = NearestNeighbors(n_neighbors=20, algorithm='auto').fit(self.X)
        else:
          self.nn = NearestNeighbors(n_neighbors=len(json_data["Data"]), algorithm='auto').fit(self.X)

    def load_data(self, json_data):
        for entry in json_data['Data']:
            entry["Title"] = str(entry["Title"]) if str(entry["Title"]) != "nan" else ""
            entry["Abstract"] = str(entry["Abstract"]) if str(entry["Abstract"]) != "nan" else ""
            self.patents.append(entry)

    def find_most_related_patents(self, query):
        query_vector = self.vectorizer.transform([query])
        distances, indices = self.nn.kneighbors(query_vector)
        related_patents = [(self.patents[i], distances[0][idx]) for idx, i in enumerate(indices[0])]
        related_patents_sorted = sorted(related_patents, key=lambda x: x[1], reverse=True)
        result=[]
        for item in related_patents_sorted:
          newItem = {}
          newItem["similarity"] = np.float64(item[1])
          newItem["Title"]=str(item[0]["Title"])
          newItem["Abstract"]=str(item[0]["Abstract"])
          newItem["Country"]=item[0]["Country"]
          newItem["Inventors"]=str(item[0]["Inventors"])
          newItem["PublicationDate"]=item[0]["Publication Date"]
          newItem["TopScore"] = np.float64(related_patents_sorted[0][1])
          result.append(newItem)
        return result
        #return related_patents
         

