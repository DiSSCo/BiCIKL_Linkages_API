from flask import Flask
from flask_app.api import predictions
from flask_app.api import repository
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

@app.route("/api")
def hello():
    return "<p>Welcome to BiCIKL Linkages</p>"


@app.route("/pollinatorOf/<taxon_id>")
def pollinator_of(taxon_id):
    # Our given taxa is a plant, we are looking for pollinators of taxon_id
    # Return plants which taxon_id is a pollinator of
    relation = "pollinates"
    is_subject = False

    observed_dict = {"Observed": repository.get_pollinators(taxon_id)}
    predicted_dict = {"Predicted": predictions.controller(relation, taxon_id, is_subject)}
    return {**observed_dict, **predicted_dict}

    # 3033668 -> pollinated by 1340470
    # Aconitium colombianum (colombian monskhood) pollinated by Bombus appositus (bumblebee)


@app.route("/pollinatedBy/<taxon_id>")
def pollinated_by(taxon_id):
    # Given a pollinator, return plants pollinated by the pollinator
    relation = "pollinates"
    is_subject = True

    observed_dict = {"Observed": repository.get_pollinated(taxon_id)}
    predicted_dict = {"Predicted": predictions.controller(relation, taxon_id, is_subject)}

    return {**observed_dict, **predicted_dict}

    # 1340470 -> pollinates 3033668
    # Bombus appositus (bumblebee) pollinates Aconitium colombianum (colombian monskhood)


@app.route("/preysOn/<taxon_id>")
def preys_on(taxon_id):
    return repository.get_prey(taxon_id)
    # 1980783 -> consumes 2685524
    # Ectropis crepuscularia (engrailed moth) consumes Abies amabilis (pacific silver fir)


@app.route("/predatedBy/<taxon_id>")
def predated_by(taxon_id):
    return repository.get_predators(taxon_id)
    # 2685524 -> consumed by 1980783
    # Abies amabilis (pacific silver fir) consumed by Ectropis crepuscularia (engrailed moth)


@app.route("/parasitizes/<taxon_id>")
def parasitizes(taxon_id):
    return repository.get_host(taxon_id)
    # 3223337 -> parasitizes 2480637
    # Campylobacter jejuni (bacteria) parasitizes accipiter nisus (swallowhawk)


@app.route("/parasitizedBy/<taxon_id>")
def hosts(taxon_id):
    return repository.get_parasite(taxon_id)
    # 2480637 -> parasitized by 3223337
    # accipiter nisus (swallowhawk) parasitized by ampylobacter jejuni (bacteria)





