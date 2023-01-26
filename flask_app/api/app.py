import json

from flask import Flask, request, jsonify

from flask_cors import CORS

# Docker
from api import predictions
from api import repository
from api import TaxonNotFoundException


# Local
'''
from api import predictions
from api import repository
from api.TaxonNotFoundException import TaxonNotFoundException
'''

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
CORS(app, allow_headers=['Content-Type'])
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)


@app.route("/hello")
def hello():
    return "<p>Welcome to BLUE BiCIKL! </p>"


@app.route("/pollinators")
def get_pollinators():
    return repository.get_all_tids(True)


@app.route("/plants")
def get_plants():
    return repository.get_all_tids(False)


@app.route("/name", methods=['GET'])
def get_name():
    taxon_id = request.json["species"]
    print(repository.get_taxon_id_from_sci_name(taxon_id))



@app.route("/pollinatorOf/<taxon_id>")
@app.route("/pollinatorOf")
def pollinator_of(taxon_id=None):
    # Our given taxa is a plant, we are looking for pollinators of taxon_id
    # Return plants which taxon_id is a pollinator of
    if taxon_id is None:
        species_name = request.json["species"]
        if species_name is None:
            raise TaxonNotFoundException("Invalid search query", 400)
        taxon_id = repository.get_taxon_id_from_sci_name(species_name)

    print(taxon_id)

    relation = "pollinates"
    # Taxon of interest is NOT a subject
    is_subject = False
    strict = False

    # Check input args

    conf = request.args.get("confidence")
    if not conf:
        conf = 0.5

    if not check_args(conf): return "invalid arguments, check confidence is float between 0 and 1", 400

    taxon_info = repository.get_input_taxonomy(taxon_id)
    if not taxon_info:
        return "Taxon not found", 404

    queried_dict = {"Input": taxon_info}
    observed_dict = {"Observed": repository.get_interactions(taxon_id, relation, is_subject)}
    predicted_dict = {"Predicted": predictions.controller(relation, taxon_id, is_subject, conf, strict)}

    return {**queried_dict, **observed_dict, **predicted_dict}

    # 3033668 -> pollinated by 1340470
    # Aconitium colombianum (colombian monskhood) pollinated by Bombus appositus (bumblebee)


@app.route("/pollinatedBy/<taxon_id>")
@app.route("/pollinatedBy")
def pollinated_by(taxon_id=None, conf=0.95):
    # Given a pollinator, return plants pollinated by the pollinator
    if taxon_id is None:
        species_name = request.json["species"]
        if species_name is None:
            raise TaxonNotFoundException("Invalid search query", 400)
        taxon_id = repository.get_taxon_id_from_sci_name(species_name)

    relation = "pollinates"
    is_subject = True
    conf = request.args.get("confidence")
    if not conf:
        conf = 0.5

    strict = False

    if not check_args(conf): return "invalid arguments, check confidence is float between 0 and 1", 400

    taxon_info = repository.get_input_taxonomy(taxon_id)
    if not taxon_info:
        return "Taxon not found", 404

    queried_dict = {"Input": taxon_info}
    observed_dict = {"Observed": repository.get_interactions(taxon_id, relation, is_subject)}
    predicted_dict = {"Predicted": predictions.controller(relation, taxon_id, is_subject, conf, strict)}

    return {**queried_dict, **observed_dict, **predicted_dict}

    # 1340470 -> pollinates 3033668
    # Bombus appositus (bumblebee) pollinates Aconitium colombianum (colombian monskhood)


@app.route("/predatorOf/<taxon_id>")
@app.route("/predatorOf")
def predator_of(taxon_id=None):
    if taxon_id is None:
        species_name = request.json["species"]
        if species_name is None:
            raise TaxonNotFoundException("Invalid search query", 400)
        taxon_id = repository.get_taxon_id_from_sci_name(species_name)
    relation = "preysOn"
    is_subject = False

    queried_dict = {"Input": repository.get_input_taxonomy(taxon_id)}
    observed_dict = {"Observed": repository.get_interactions(taxon_id, relation, is_subject)}

    predicted_dict = {"Predicted": []}
    return {**queried_dict, **observed_dict, **predicted_dict}

    # 1035290 (pilicornis) preys on 1036203 (properans)


@app.route("/predatedBy/<taxon_id>")
@app.route("/predatedBy")
def predated_by(taxon_id=None):
    if taxon_id is None:
        species_name = request.json["species"]
        if species_name is None:
            raise TaxonNotFoundException("Invalid search query", 400)
        taxon_id = repository.get_taxon_id_from_sci_name(species_name)
    relation = "preysOn"
    is_subject = True

    queried_dict = {"Input": repository.get_input_taxonomy(taxon_id)}
    observed_dict = {"Observed": repository.get_interactions(taxon_id, relation, is_subject)}

    predicted_dict = {"Predicted": []}
    return {**queried_dict, **observed_dict, **predicted_dict}


@app.route("/parasitizes/<taxon_id>")
@app.route("/parasitizes")
def parasitizes(taxon_id=None):
    if taxon_id is None:
        species_name = request.json["species"]
        if species_name is None:
            raise TaxonNotFoundException("Invalid search query", 400)
        taxon_id = repository.get_taxon_id_from_sci_name(species_name)
    relation = "parasiteOf"
    is_subject = False

    queried_dict = {"Input": repository.get_input_taxonomy(taxon_id)}
    observed_dict = {"Observed": repository.get_interactions(taxon_id, relation, is_subject)}

    predicted_dict = {"Predicted": []}
    return {**queried_dict, **observed_dict, **predicted_dict}

    # 1007770 (membranacea) parasiteOf 5422328 (pyrifera)


@app.route("/parasitizedBy/<taxon_id>")
@app.route("/parasitizedBy")
def hosts(taxon_id=None):
    if taxon_id is None:
        species_name = request.json["species"]
        if species_name is None:
            raise TaxonNotFoundException("Invalid search query", 400)
        taxon_id = repository.get_taxon_id_from_sci_name(species_name)
    relation = "parasiteOf"
    is_subject = True

    queried_dict = {"Input": repository.get_input_taxonomy(taxon_id)}
    observed_dict = {"Observed": repository.get_interactions(taxon_id, relation, is_subject)}

    predicted_dict = {"Predicted": []}
    return {**queried_dict, **observed_dict, **predicted_dict}

    # 1007770 (membranacea) parasiteOf 5422328 (pyrifera)


@app.route("/predict", methods=["GET", "POST"])
def predict():
    request_data = request.get_json()

    relation = request_data['relation']
    is_subject = request_data['is_subject']
    taxon_id = request_data['taxon_id']
    check = request_data['check']
    confidence = request_data["confidence"]
    strict = False

    queried_dict = {"Input": repository.get_input_taxonomy(taxon_id)}

    predicted_dict = {"Predicted": predictions.controller(relation, taxon_id, is_subject, confidence, strict, check)}

    return {**queried_dict, **predicted_dict}


@app.route("/interactions", methods=["GET"])
def interactions():
    interactions_list = {
        "pollinates": [
            ['pollinatorOf', 'Pollinator of'],
            ['pollinatedBy', 'Pollinated by']
        ],
        "preysOn": [
            ['predatorOf', 'Predator of'],
            ['predatedBy', 'Predated by']
        ],
        "parasiteOf": [
            ['parasitizes', 'Parasitizes'],
            ['parasitizedBy', 'Parasitized by']
        ]
    }

    return {"Interactions": interactions_list}


def check_args(conf):
    if type(conf) != float or conf > 1 or conf < 0:
        return False
    return True


@app.errorhandler(TaxonNotFoundException)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
