from sqlalchemy import select, and_
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

# Docker
from bin import db_connections
from api import Tables as db

# Local
# from flask_app.bin import db_connections
# from api import Tables as db



def flatten(l):
    # Flatten a list (usually the results of a sqlalchemy query)
    return [item for sublist in l for item in sublist]


def get_all_tids(is_subject):  # Returns pollinators if true (subjects), plants if false (targets)
    engine = create_engine(db_connections.DB_CONNECT, echo=False, future=True)
    if is_subject:
        stmt = select(db.Interactions.subject_taxon_id) \
            .where(db.Interactions.relation_type == 'pollinates')
    else:
        stmt = (select(db.Interactions.target_taxon_id)
                .where(db.Interactions.relation_type == 'pollinates'))

    with Session(engine) as session:
        result = session.execute(stmt).all()
    return flatten(result)


def get_input_taxonomy(taxon_id):
    engine = create_engine(db_connections.DB_CONNECT, echo=False, future=True)

    #stmt = select(db.Species.kingdom, db.Species.phylum, db.Species.ord, db.Species.fam, db.Species.genus,
    #              db.Species.species, db.Species.sci_name).where(db.Species.taxon_id == taxon_id)

    stmt = select(db.Species).where(db.Species.taxon_id == taxon_id)
    with Session(engine) as session:
        result = flatten(session.execute(stmt).all())

    result_records = []
    for q in result:
        d = q.to_dict()
        result_records.append(d)

    return result_records


def get_taxon_id_from_sci_name(sciName):
    stmt = select(db.Species.taxon_id).where(
        db.Species.sci_name == sciName)

    engine = create_engine(db_connections.DB_CONNECT, echo=False, future=True)
    with Session(engine) as session:
        try:
            result = session.execute(stmt).one()
            return result[0]
        except NoResultFound as e:
            message = sciName + " not present in database"
            return ""


def get_interactions(taxon_id, relation, isSubject):
    if isSubject:
        stmt = select(db.Interactions.target_taxon_id).where(and_(
            db.Interactions.subject_taxon_id == taxon_id,
            db.Interactions.relation_type == relation))
    else:
        stmt = select(db.Interactions.subject_taxon_id).where(and_(
            db.Interactions.target_taxon_id == taxon_id,
            db.Interactions.relation_type == relation))

    return get_relation(stmt)


def get_relation(stmt):
    engine = create_engine(db_connections.DB_CONNECT, echo=False, future=True)
    with Session(engine) as session:
        result = session.execute(stmt).all()
        result_ids = [r[0] for r in result]

        stmt = select(db.Species). \
            where(db.Species.taxon_id.in_(result_ids))
        result = flatten(session.execute(stmt).all());

    result_records = []
    for q in result:
        d = q.to_dict()
        result_records.append(d)

    return result_records
