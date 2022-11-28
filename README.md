# BiCIKL_Linkages_API
Here, we outline the functionality of the Biotic Linkages United Explorer (BLUE) API. This prototype is a RESTful API capable of predicting interactions between organisms using a machine learning classifier. It also returns observed interactions, as they have been recorded in bibliographic references, enabling the user to make inferences about unseen interactions.

The BLUE API uses GBIF Taxon Ids to identify unique species. In the future, it will be desirable to accept species names as well as taxon ids. This can be achieved by querying the GBIF taxonomic backbone in a layer between the user and the application. 

## Endpoints

The API is accessible through the DNS ec2-18-134-210-210.eu-west-2.compute.amazonaws.com/. This section gives an overview of available endpoints.

**/hello**

Confirms connection to API

**/plants** 

Returns taxon_id of all the plants in the database that have one or more associated pollinator

**/pollinators**

Returns taxon_id of all pollinators in the database

**/pollinatorOf/{taxon_id}**

*Body (Optional):*

Returns pollinators of the taxon of interest, checking against all pollinators in the database. Returned values include both observed interactions and predicted values; for the latter, a confidence value is given. 

{
   "conf":0.5
}


The optional parameter “conf” allows the user to set the minimum confidence threshold to return potential matches. The default value for “conf” is 0.5. 

**/pollinatedBy/{taxon_id}**

Returns plants pollinated by the taxon of interest by classifying all entities in the database. Like the /pollinatorOf endpoint, this endpoint returns both observed and predicted values. This endpoint can take the same request body as /pollinatorOf as well. 

**/predict**

This endpoint accepts specific taxa to be checked against the taxon of interest, returning confidence values for the most likely taxa. 

*Body (mandatory):*
{

  "relation":"pollinates",

  "is_subject":true,

  "taxon_id": 1314881,

  "check": [2928234, 2964138, 2781074, 111, 9999],

  "confidence":0.6

}

**relation:** Interaction of interest. Currently, only “pollinates” is supported.

**is_subject:** Interactions are conceptualized as: *Subject X <interacts with> Target Y*. If this flag is set to true, BLUE will return targets of the relation (i.e. Ys). If the flag is false, it will return subjects of the interaction (i.e. Xs). 

**taxon_id:** GBIF taxon id for the taxon of interest

**check:** List of taxon ids to validate described relationship with taxon of interest

**confidence:** Minimum confidence for returned predictions. Decimal value. 

## Architecture

### API
The BLUE API is a RESTful API built using the Flask framework.

The API interfaces with the database using the SQLAlchemy toolkit. Upon receiving a request, the API retrieves taxonomic information about the taxon of interest from the database. If the user does not specify a list of taxa to check (i.e. using the /predict endpoint), the API will check all appropriate taxa stored in the database. It evaluates each pair, and returns matches with a confidence level above a specified threshold. 

“Appropriate taxa” are determined by looking at the interaction type and the phylum the taxon of interest belongs to. A list of interaction rules was developed from literature to narrow down the data supplied to the classifier. Using the interaction rules, the program is able to select only species belonging to likely phyla and classify those species, instead of all possible species in the database. Subsetting at the phylum level is still broad enough to allow the classifier to make meaningful decisions while omitting ecologically impossible matches (e.g. a plant pollinating a mollusc or a vertebrate parasitizing a bacterium). 

### Classifier
The classifier used is a SMOTE random forest classifier implemented using the Sci Kit Learn python package. The random forest classifier was chosen because it trains quickly relative to other machine learning models and it performs well. See this blog post for an overview of how random forest classifiers work. Using SMOTE, or Synthetic Minority Oversampling Technique, allows the classifier to adapt better to highly skewed data (i.e. more data in one class than another). 

The classifier predicts how likely a pollinator-plant pair is to be a valid match based on taxonomic information.  Given a taxon of interest and a list of potential matches, the classifier is able to identify the most likely valid pairs.  The features used to train the classifier are: kingdom, phylum, order, family, genus, species, and scientific name for both plants and pollinators (this is the same list of features required to classify an interaction). When making predictions, the classifier is given a table, wherein each row represents a pollinator-plant pair’s taxonomy. 


### Database
Data is stored on a PostgreSQL relational database hosted on Amazon Web Services. Species was obtained from the Global Biodiversity Interactions and GBIF Databases. The integer mapping required to transform taxon data into a form the classifier can process is also stored in the database, in the classifier_tools table.  

What is notably missing from this database is the classifier itself, as well as the scaler used as a preprocessing step. Relational databases are not well-suited for storing unstructured data such as a machine learning model. The classifier is currently stored locally. A more desirable solution would be to store the classifier in an object storage facility, such as Amazon’s S3 service. In the Postgres database, there should be a pointer to the object storage. 

### Deployment
The BLUE API is run on a Gunicorn WSGI server, which is behind an Nginx reverse-proxy. The Nginx reverse-proxy is a dedicated HTTP server that handles incoming requests securely for Gunicorn. The Nginx reverse-proxy accepts requests at port 80 and forwards them internally to the Gunicorn server, which is listening at port 5000. The entire setup is Dockerized into two images (one for Flask and Gunicorn, and one for Nginx) and deployed on an Amazon Web Service EC2 server. 
