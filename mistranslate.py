import google.cloud.translate_v2 as tl
import os,random,json

#Set up environment variables when imported
__location__ = os.path.join(os.getcwd(),os.path.dirname(__file__))
gac_filepath = os.path.join(__location__, 'gac-key.json')
conf_filepath = os.path.join(__location__, 'config.json')
cf = open(gac_filepath)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(__location__, 'gac-key.json')

class mt_Client(tl.Client):
    config = {'max-tl-chain': 20}
    cfgfile = None
    try:
        cfgfile = open(conf_filepath)
        cfgjson = cfgfile.read()
        config = json.loads(cfgjson)
    except FileNotFoundError:
        print("WARNING: config.json file not found; using defaults.")
            
    def __init__(self):
        #Set environment variable
        #Run parent init
        tl.Client.__init__(self)
        self.langdata = self.get_languages()
    
    #Update language database
    def update_languages(self):
        self.langdata = self.get_languages()
    
    #Check whether or not a language code is valid.
    def get_langcode(self,langcode,name=False):
        if not isinstance(langcode,str):
            raise TypeError('Language code must be a string')
        for i in self.langdata:
            if langcode.lower() == i['language'].lower() or langcode.lower() == i['name'].lower():
                return i['name'] if name else i['language']
        #If no matches occur, the code is invalid
        raise ValueError("Invalid language code '{0}'".format(langcode))
        
    def chain_translate(self,inputstr,listmode,outputlang=None,iters=0,inputlang=None,langlist=None):
        """Run a string of text through the translator a set number of times, using random languages for each iteration. Returns a string.
        
        REQUIRED VALUES:
        inputstr  : The input string of text.
        listmode  : Specifies whether the translation languages will be restricted. 0 = None; all languages may be used. 1 = Blacklist; languages in langlist will not be used. 2 = Whilelist; only languages in langlist will be used. 3 = Queue; input will be translated with the languages in langlist, in the order given.

        
        OPTIONAL VALUES:
        outputlang: The language to translate the resultant text into. Defaults to config variable 'default-lang ('en' if config is absent.).
        iters     : An integer defining the number of additional translations to be performed. Default allowed range is 1~20. Default value is 0 (standard translation).
        inputlang : The language code for input. If omitted, automatically determines language.
        langlist  : A list of strings containing language codes, or string of comma-separated language codes, to be used as either a language blacklist, whitelist or queue, as specified by listmode.
        """
        #Check parameter values
        if not isinstance(inputstr,str):
            raise TypeError(f'Input must be a string. Received value: {type(inputstr)} ({inputstr})')
        elif not inputstr:
            raise ValueError('Input must not be blank.')
            
        if not isinstance(listmode,int):
            raise TypeError('listmode must be an integer.')
        if listmode < 0 or listmode > 3:
            raise ValueError('listmode must be between 0 and 3.')
        
        if listmode != 0:
            if isinstance(langlist,str):
                langlist = langlist.split(',')
            if isinstance(langlist,list):
                for i in langlist:
                    i = self.get_langcode(i)
            elif langlist == None:
                raise TypeError('No language list was provided; the current flag(s) set require a language list.')
            else:
                raise TypeError('Language list must be a comma-separated list of language codes with no spaces or other symbols.')
        
        if (listmode == 1 or listmode == 2):
            if not isinstance(iters,int):
                raise TypeError('Number of iterations must be a valid integer')
            elif iters < 1 or iters > config['max-tl-chain']:
                raise ValueError(f"Number of iterations must be between 1 and {config['max-tl-chain']}.")
        
        if outputlang != None:
            outputlang = self.get_langcode(outputlang)
        
        if inputlang != None:
            inputlang = self.get_langcode(inputlang)
        
        
        
        #Once all data is validated, proceed with translation
        rval = {}
        rval['input'] = inputstr
        rval['inputlang'] = inputlang
        rval['iters'] = []
        curinput = inputstr
        if listmode == 3:
            iters = len(langlist)
        for i in range(iters):
            #Select a random language to translate to
            if listmode == 3:
                thislang = langlist[i]
            elif listmode == 2:
                thislang = random.choice(langlist)
            else:
                thislang = random.choice(self.langdata)['language']
            while listmode == 1 and thislang in langlist:
                thislang = random.choice(self.langdata)['language']
            #Translate and save this iteration
            result = self.translate(curinput,thislang,'text',inputlang)
            curinput = result['translatedText']
            if rval['inputlang'] == None:
                rval['inputlang'] = result['detectedSourceLanguage']
            #Discard the inputlang value for subsequent translations
            inputlang = None
            rval['iters'].append({'language':thislang,'result':curinput})
        #Finally, translate the result to the target language (unless listmode is 3)
        if listmode != 3:
            result = self.translate(curinput,outputlang,'text')
            rval['iters'].append({'language':outputlang,'result':result['translatedText']})
        return rval
