# MLOPS - Sujet 2

Dans ce projet vous aurez à mettre en production un modèle de machine learning de votre choix.

Le déploiement du modèle devra se faire automatique via un script simple. 

Il faudra que le modèle puisse gérer une certaine charge. Vous pourrez soit faire du batch processing / une API HTTP ou du streaming. 

Il faudra que le système soit capable de : 

- soit de se réentraîner tout seul régulièrement grâce à des données nouvellement labelisée
- soit de faire remonter des alertes si il existe des risques que le modèle ne marche plus (distributional shift)

Bonus : le modèle sera packagé dans un conteneur docker ou sera déployé via Kubernetes / kubeflow


## Application

Cette application consiste à faire de l'analyse de sentiment.
Pour chaque texte anglais en entrée, l'application détermine s'il est **négatif** ou **positif**

Pour démarrer l'application

```
docker-compose up --build
```

L'application est ainsi mise en production via le gestionaire d'API Rest : **FastAPI**. Elle est disponible à l'adresse `http://localhost:8080/`

### L'API
---
POST : `/predict`
```json
{"text": "I love you"}
```
Retourne :
```json
{"prediction": "positive"}
```
OU
```json
{"prediction": "negative"}
```

---

POST : `/retrain`
```json
{
    "text": "I love you",
    "label": 1
}
```
---
GET : `/drift`

Cela retourne un booléen qui indique si le modèle a détecté un décalage de distribution
```json
{"drift": true}
```
---
GET : `/generate_drift`

Cela génère un décalage de distribution dans le modèle


## Modèle 

Le modèle d'apprentissage automatique est un classifieur NaiveBayes multinomial.
Il vecotrise les textes d'entrée en attribuant à chaque mot de vocabulaire son nombre d'occurences

### Pipeline
```
'Texte'
 -> Lower case
 -> Remove punctuation
 -> Count vectorizer
 -> Multinomial Naive Bayes
 -> Prediction (0 ou 1)
```

### Données

Les données d'entraînement sont issues de [IMDB](https://www.imdb.com/interfaces/)

## Streaming

Le programme utilise la Stream de **RabbitMQ** pour récupérer les données d'entrée et les faire transiter vers le modèle de ML en passant par la base de données **MongoDB**.

**RabbitMQ** renvoie le résultat du modèle après que la requête ait été traitée par le stream consumer et le modèle de ML.

## Base de données

La base de données **MongoDB** est utilisée pour stocker les données d'entrée et les résultats du modèle de ML.
