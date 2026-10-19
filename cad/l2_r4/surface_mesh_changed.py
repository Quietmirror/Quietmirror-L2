"""Remesh only source-modified parts; immutable BODY mesh is retained."""
from surface_mesh import main
if __name__=='__main__':main(['SIDE_FRONT_KEY','SIDE_REAR_KEY','SF_RETAINER','SR_RETAINER','WHEEL_CARRIER'])
