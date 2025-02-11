import joblib
import numpy as np
import matplotlib.pyplot as plt

KMEANS_PATH = "data_latihan/trained_data.joblib"

data = joblib.load(KMEANS_PATH)

print("Komponen yang tersimpan:")
print(data.keys())

# model
kmeans = data['kmeans']
print("total:", kmeans.n_clusters)
print("cluster:", kmeans.cluster_centers_[0][:5])

# vector
tfidf = data['tfidf_vectorizer']
print("\nvector tfidf:", tfidf.get_feature_names_out()[:10])

# pola
replacements = data['dynamic_replacements']
print("\npola :")
for pattern in list(replacements.keys())[:3]:
    print("Pola:", pattern.pattern, "→ ganti:", replacements[pattern])

# plot cluster 2d
if kmeans.cluster_centers_.shape[1] >= 2:
    plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s=100)
    plt.title("cluster :")
    plt.show()
else:
    print("besar skali")