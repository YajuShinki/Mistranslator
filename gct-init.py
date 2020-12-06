import google.cloud.translate_v2 as tl
import sys,os

#set environment variable
__location__ = os.path.join(os.getcwd(),os.path.dirname(__file__))
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(__location, 'gct-key.json')

tlclient = tl.Client()

