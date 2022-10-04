import math
import os
import warnings

import joblib
import numpy as np
from sqlalchemy import select, and_
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from bin import db_connections
from api import Tables as db

#from flask_app.bin import db_connections
#from flask_app.api import Tables as db

'''
TODO
    Train classifier on taxon ids instead of ordinal integers 
    - Get taxon ids for higher-level groups and upload it to db
    
    Do other relationships: eats, parasitizes

'''

'''
*** Relations Overview ***
    parasiteOf
        Subject: parasite
        Target: host
        Includes relationships: hasHost, endoparasiteOf, parasitoidOf, ectoparasiteOf, endoparasitoidOf, ectoparasitoidOf, livesInsideOf, laysEggsOn, pathogenOf
    preysOn
        Subject: Predator
        Target: Prey
        Includes relationships: eats
    pollinates
        Subject: Pollinator
        Target: Plant
        Includes relationships: NA
'''


# Quality of life

def flatten(l):
    # Flatten a list (usually the results of a sqlalchemy query)
    return [item for sublist in l for item in sublist]


def list_diff(a, b):
    return list(set(a) - set(b))

# Get Taxonomic Info

def get_species_info(t_id):
    # Given a taxon id, return its taxonomy levels
    stmt = select(db.Species.kingdom, db.Species.phylum, db.Species.ord, db.Species.fam, db.Species.genus,
                  db.Species.species, db.Species.sci_name). \
        where(db.Species.taxon_id == t_id)
    result = session.execute(stmt).first()
    if not result:
        return []

    return list(result)


def get_phyla(relation, phylum, is_subject_query):
    # Given a relationship and a phylum of interest, return phyla that have that relationship with the given phylum
    # is_subject_query flag reflects which "side" of the relationship we're interested in

    # If we're given the subject, return the target of the relationship
    if is_subject_query:
        stmt = select(db.Relation_rules.target_phylum). \
            where(and_(db.Relation_rules.subject_phylum == phylum, db.Relation_rules.relation_type == relation))

    # If we're given the target, return the subject of the relationship
    else:
        stmt = select(db.Relation_rules.subject_phylum). \
            where(and_(db.Relation_rules.target_phylum == phylum, db.Relation_rules.relation_type == relation))

    result = session.execute(stmt).all()
    # Return
    return flatten(result)


def get_species_list_from_phyla(phyla):
    # Given a list of phyla and the taxon_map used to train a specific classifier, return a list of eligible species
    species_list_full = []

    for phylum in phyla:
        # Given a phylum, get full taxonomy and ids of all species under that phylum
        stmt = select(db.Species.taxon_id, db.Species.kingdom, db.Species.phylum, db.Species.ord, db.Species.fam,
                      db.Species.genus, db.Species.species, db.Species.sci_name). \
            where(db.Species.phylum == phylum)
        species_list_full = species_list_full + session.execute(stmt).all()

    species_list_taxonomy = [sp[1:] for sp in species_list_full]
    species_list_tid = [sp[0] for sp in species_list_full]

    return species_list_taxonomy, species_list_tid
    # return species_subset, int_map_to_tid


def get_taxonomy_from_species_list(taxon_ids):
    stmt = select(db.Species.taxon_id, db.Species.kingdom, db.Species.phylum, db.Species.ord, db.Species.fam,
                      db.Species.genus, db.Species.species, db.Species.sci_name).filter(db.Species.taxon_id.in_(taxon_ids))
    species_list_full = session.execute(stmt).all()

    species_list_taxonomy = [sp[1:] for sp in species_list_full]
    species_list_tid = [sp[0] for sp in species_list_full]

    return species_list_taxonomy, species_list_tid

# taxon_int mapping
# When the classifier was trained, it used a mapping that transformed each taxonomic level into an integer
# In order to classify a taxon, we need to return it to the data we received it


def map_species_to_int(species_list, taxon_ids, taxon_map):
    # Given a list of species/taxon ids, return a list of taxon_int mapped taxa
    # Also return the specific mapping, as the taxonomic mapping is not ambiguous

    # Map each row of potential species to their appropriate int mapping
    species_int_list = [map_taxonomy_int_row(row, taxon_map) for row in species_list]

    # Save the int-mapped to taxon ids to a dictionary
    # Where the taxon_int mapping (as a string) is the key and the taxon id is the value
    map_int_to_tid = save_mapping(taxon_ids, species_int_list)

    # Filter out empty lists (i.e. unmapped species)
    species_int_list = list(filter(None, species_int_list))

    return species_int_list, map_int_to_tid

    # Because the taxonomy of pollinators and plants are independently classified, you can have [0, 0, 0, 0] as a pollinator and [0, 0, 0, 0] as a plant
    # Say you have plant [1, 1, 1, 1] that is pollinated by pollinator [0, 0, 0, 0]
    # The combination [0, 0, 0, 0, 0, 1, 1, 1, 1] is thus a correct result
    # But you could have a plant [0, 0, 0, 0], which then would also "pollinate" the plant
    # This would never be given to the classifer due to Relation_Rules, however


def save_mapping(taxon_ids, int_mappings):
    # This will be used to reverse lookup taxon ids
    map_tracker = {}

    for int_tax, t_id in zip(int_mappings, taxon_ids):
        if not int_tax:  # Don't bother mapping
            continue
        map_tracker[str(int_tax)] = t_id

    return map_tracker


def map_taxonomy_int_row(row, taxon_map):
    # Given a row of taxonomy levels (strings), map each value to its int mapping
    new_row = []

    try:
        new_row = [taxon_map[r] for r in row]
    except KeyError:
        # If one taxonomy level is not in our int mapped, the row will be blank
        # e.g. in the case where up to the family is mapped, but a specific species is not
        warnings.warn("Potential matching taxon not int-mapped")
    return new_row


def get_taxon_map(relation, strict):
    # Given a relationship (linkage), return the appropriate int mapping used to train the classifier
    if strict:
        relation = relation + "_strict" # key for the "stricter" taxon_map stored in the database

    stmt = select(db.Classifier.int_mapping).where(db.Classifier.relation_type == relation)
    result = session.execute(stmt).first()
    return result[0]


# We've made a shortlist of potential species. Now, let's see how well they go with our species of interest

def classify_results(taxon_int_mapping, relation, thresh, strict):
    # transform mapping to np array
    int_arr = np.array(taxon_int_mapping)

    # If we only have 1 element to classify, we reshape this array to keep sklearn happy
    if int_arr.ndim == 1:
        int_arr = int_arr.reshape(1, -1)

    pwd = os.getcwd()

    if relation == "pollinates":
        if strict:
            #model_path = os.path.join(pwd, "../classifiers/SMOTE_Model_Strict_model")
            #scaler_path = os.path.join(pwd,  "../classifiers/SMOTE_Model_Strict_scaler")
            model_path = os.path.join(pwd, os.path.relpath("classifiers/SMOTE_Model_Strict_model"))
            scaler_path = os.path.join(pwd, os.path.relpath("classifiers/SMOTE_Model_Strict_scaler"))
        else:
            #model_path = os.path.join(pwd, "../classifiers/SMOTE_Model_model")
            #scaler_path = os.path.join(pwd, "../classifiers/SMOTE_Model_scaler")

            model_path = os.path.join(pwd, os.path.relpath("classifiers/SMOTE_Model_model"))
            scaler_path = os.path.join(pwd, os.path.relpath("classifiers/SMOTE_Model_scaler"))

    else:
        warnings.warn("Selected relation not currently supported for ML classification")
        return

    # Unpickle classifier and scaler
    RFC = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # Normalize input data
    int_arr = scaler.transform(int_arr)

    # Make predictions
    predictions = RFC.predict_proba(int_arr)

    # Select values where confidence is above a certain threshold
    idx = list(np.where(predictions[:, 1] >= thresh))[0]

    top_taxa = [taxon_int_mapping[i] for i in idx]
    confidence = [predictions[i, 1] for i in idx]

    return top_taxa, confidence


# Resolve and read results


def reverse_lookup(map_dict, top_taxa, is_subject_query):
    mid = math.floor((len(top_taxa[0]) / 2))
    if is_subject_query:
        # If it is a subject_query, we need to trim the LEFT half of the top_taxa list
        # This will leave us with our targets
        top_taxa_str = [str(t[mid:]) for t in top_taxa]

    else:
        # If it is a target_query, we need to tirm the RIGHT half of the top_taxa list
        # Leaving us with subjects
        top_taxa_str = [str(t[:mid]) for t in top_taxa]

    # Go from taxon int_mapping to taxon_ids
    top_taxa_id = [map_dict[k] for k in top_taxa_str]

    return top_taxa_id


def resolve_taxa(top_taxa_ids, confidence):
    stmt = select(db.Species). \
        where(db.Species.taxon_id.in_(top_taxa_ids))

    result = flatten(session.execute(stmt).all())
    result_records = []
    for r, c in zip(result, confidence):
        d = r.to_dict()
        d["confidence"] = c
        result_records.append(d)

    return result_records



def append_missed_taxa(missed_taxa, taxa):
    for tid in missed_taxa:
        d = {
            "taxon_id":tid,
            "confidence":"Unknown"
        }
        taxa.append(d)
    return taxa


def append_not_int_mapped(missed_taxa , int_map_to_tid, taxon_ids):
    int_mapped_tids = list(int_map_to_tid.values())
    not_int_mapped = list_diff(taxon_ids, int_mapped_tids)

    return list(set(missed_taxa + not_int_mapped)) # Remove duplicates

# Main function of this class, calls the whole shebang

def controller(relation, taxon_id, is_subject_query, conf_thresh, strict, check_list=[]):

    null_response = []  # just in case

    # Select appropriate int mapping based on our relation
    taxon_map = get_taxon_map(relation, strict)
    #print(taxon_map)

    # Query DB, get taxonomy of taxon of interest
    species_info = get_species_info(taxon_id)

    if not species_info:
        warnings.warn("Species not found")
        return null_response

    # Given species taxonomy, locate its particular int mapping
    species_info_int = map_taxonomy_int_row(species_info, taxon_map)

    if not species_info_int:  # If our species doesn't have an int_map, no point going any further
        return null_response

    # If no list is provided, we check all potential species at the phylum level
    if not check_list:
        # Get species phylum, determine other phyla it can have the specified relation with
        phylum = species_info[1]
        appropriate_phyla = get_phyla(relation, phylum, is_subject_query)

        # Given phyla, get species
        species_list, taxon_ids = get_species_list_from_phyla(appropriate_phyla)
        missed_taxa = []
    else:
        species_list, taxon_ids = get_taxonomy_from_species_list(check_list)
        missed_taxa = list_diff(check_list, taxon_ids) # this is the list of taxa not in the database

    '''
    This is where we could impose other restrictions on species_list
    e.g. geographic range limits
    Could also do that in the get_phyla() function (by altering the select statement)
    '''

    # Given species list, get taxon_int mapping (and save this mapping)
    species_to_check_int, int_map_to_tid = map_species_to_int(species_list, taxon_ids, taxon_map)
    #missed_taxa = append_not_int_mapped(missed_taxa, int_map_to_tid, taxon_ids)

    # If no appropriate phyla have been int-mapped, return our null response
    if not species_to_check_int:
        return append_missed_taxa(missed_taxa, [])

    if is_subject_query:
        # If our taxon is a SUBJECT, the species info int mapp will go to the LEFT of the potential matches
        pass_to_class = [species_info_int + r for r in species_to_check_int]

    else:
        # If our taxon is a TARGET, the species info int mapp will go to the RIGHT of the potential matches
        pass_to_class = [r + species_info_int for r in species_to_check_int]


    # This is where the magic happens - classify our results and get our confidence

    top_taxa, confidence = classify_results(pass_to_class, relation, conf_thresh, strict)

    if not top_taxa:
        return null_response  # If classifier doesn't return any predictions

    top_taxa_ids = reverse_lookup(int_map_to_tid, top_taxa, is_subject_query)

    taxa = resolve_taxa(top_taxa_ids, confidence)

    # Default return value, if no list was provided at the start
    if not missed_taxa:
        return taxa
    else:
        return append_missed_taxa(missed_taxa, taxa)

#0, 0, 5, 6, 71, 472, 256, 0, 0, 32, 99, 126, 765, 256


engine = create_engine(db_connections.DB_CONNECT, echo=False, future=True)
session = Session(engine)

#get_taxonomy_from_species_list(tid)

''''
strict = False
relation = "pollinates"
#taxon_map = get_taxon_map(relation, strict)


pass_to_class = [[0,0,3,92,439,464,1175,0,0,0,10,50,817,84]]
classify_results(pass_to_class, relation,0, strict) '''
