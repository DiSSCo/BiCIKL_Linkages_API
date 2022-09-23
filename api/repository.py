from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import psycopg2
import db_connections
import Tables as db



def flatten(l):
    # Flatten a list (usually the results of a sqlalchemy query)
    return [item for sublist in l for item in sublist]


def get_pollinators(taxon_id):
    stmt = select(db.Pollinates_rln.pollinator_taxon_id).where(db.Pollinates_rln.pollinated_taxon_id==taxon_id)
    return get_relation(stmt)


def get_pollinated(taxon_id):
    stmt = select(db.Pollinates_rln.pollinated_taxon_id).where(db.Pollinates_rln.pollinator_taxon_id == taxon_id)
    return get_relation(stmt)


def get_predators(taxon_id):
    stmt = select(db.Consumer_rln.consumers_taxon_id).where(db.Consumer_rln.consumed_taxon_id == taxon_id)
    return get_relation(stmt)


def get_prey(taxon_id):
    stmt = select(db.Consumer_rln.consumed_taxon_id).where(db.Consumer_rln.consumers_taxon_id == taxon_id)
    return get_relation(stmt)


def get_parasite(taxon_id):
    stmt = select(db.Parasite_rln.parasite_taxon_id).where(db.Parasite_rln.host_taxon_id == taxon_id)
    return get_relation(stmt)


def get_host(taxon_id):
    stmt = select(db.Parasite_rln.host_taxon_id).where(db.Parasite_rln.parasite_taxon_id == taxon_id)
    return get_relation(stmt)


def get_relation(stmt):
    session = Session(engine)
    result = session.execute(stmt).all()
    result_ids = [r[0] for r in result]

#    stmt = select(db.Species.kingdom, db.Species.phylum, db.Species.ord, db.Species.fam, db.Species.genus, db.Species.species).\
#        where(db.Species.taxon_id.in_(result_ids))
    stmt = select(db.Species).\
        where(db.Species.taxon_id.in_(result_ids))
    result = flatten(session.execute(stmt).all());

    # result_records = {r.to_dict for r in result}
    result_records = []
    for q in result:
        d = q.to_dict()
        result_records.append(d)

    #result_records = {"observed": result_records}

    return result_records






engine = create_engine(db_connections.DB_CONNECT, echo=False, future=True)




