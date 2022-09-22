from sqlalchemy import Column, ForeignKey, Integer, String, Float, JSON
from sqlalchemy_serializer import SerializerMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Species(db.Model, SerializerMixin):
    __tablename__ = 'species'
    taxon_id = Column(Integer, primary_key=True)

    kingdom = Column(String(255))
    phylum = Column(String(255))
    ord = Column(String(255))
    fam = Column(String(255))
    genus = Column(String(255))
    species = Column(String(255))


class Region(db.Model):
    __tablename__ = 'region'
    region_id = Column(Integer, primary_key=True)
    region_name = Column(String(255))


class Pollinates_rln(db.Model):
    __tablename__ = 'x_pollinates_y'
    pollinator_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), primary_key=True)
    pollinated_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), primary_key=True)
    confidence = Column(Float)


class Consumer_rln(db.Model):
    __tablename__= 'x_consumes_y'
    consumers_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), primary_key=True)
    consumed_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), primary_key=True)
    confidence = Column(Float)


class Parasite_rln(db.Model):
    __tablename__= 'x_parasitizes_y'
    parasite_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), primary_key=True)
    host_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), primary_key=True)
    confidence = Column(Float)


class Relation_rules(db.Model):
    __tablename__='relation_rules'
    subject_kingdom = Column(String(255))
    subject_phylum = Column(String(255), primary_key=True)
    target_kingdom = Column(String(255))
    target_phylum = Column(String(255), primary_key=True)
    relation_type = Column(String(255), primary_key=True)


class Relation_int_mapping(db.Model):
    __tablename__='relation_int_mapping'
    relation_type = Column(String(255), primary_key=True)
    int_mapping = Column(JSON)



    #,

    #pollinator_taxon_id = relationship('Species', backref='pollinator', lazy='dhynamic', foreign_keys=Species. )

    #payments = db.relationship('Payment', backref='payer', lazy='dynamic', foreign_keys='Payment.uidPayer')

    #pollinated_taxon_id = Column(Integer, ForeignKey('species.taxon_id'), PrimaryKey=True)

