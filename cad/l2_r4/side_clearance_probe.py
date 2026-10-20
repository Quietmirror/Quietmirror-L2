"""Nine local poses per key; debugging only, not the final G5 acceptance."""
import os
os.environ['R4_SIDE_LOCAL_PROBE']='1'
from side_functional_checks import main
if __name__=='__main__':main()
