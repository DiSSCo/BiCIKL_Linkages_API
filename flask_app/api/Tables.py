from sqlalchemy import Column, ForeignKey, Integer, String, Float, JSON, LargeBinary
from sqlalchemy_serializer import SerializerMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Species(db.Model, SerializerMixin):
    __tablename__ = 'species_corrected'
    taxon_id = Column(Integer, primary_key=True)

    kingdom = Column(String(255))
    phylum = Column(String(255))
    ord = Column(String(255))
    fam = Column(String(255))
    genus = Column(String(255))
    species = Column(String(255))
    sci_name = Column(String(255))


class Interactions (db.Model):
    __tablename__ = 'interactions'
    subject_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), primary_key=True)
    target_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), primary_key=True)
    relation_type = Column(String(255), primary_key=True)


class Region(db.Model):
    __tablename__ = 'region'
    region_id = Column(Integer, primary_key=True)
    region_name = Column(String(255))

class Relation_rules(db.Model):
    __tablename__='relation_rules'
    subject_kingdom = Column(String(255))
    subject_phylum = Column(String(255), primary_key=True)
    target_kingdom = Column(String(255))
    target_phylum = Column(String(255), primary_key=True)
    relation_type = Column(String(255), primary_key=True)


class Classifier(db.Model):
    __tablename__='classifier_tools'
    relation_type = Column(String(255), primary_key=True)
    int_mapping = Column(JSON)
    classifier = Column(LargeBinary)
    scaler = Column(LargeBinary)

    #,

    #pollinator_taxon_id = relationship('Species', backref='pollinator', lazy='dhynamic', foreign_keys=Species. )

    #payments = db.relationship('Payment', backref='payer', lazy='dynamic', foreign_keys='Payment.uidPayer')

    #pollinated_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), PrimaryKey=True)

