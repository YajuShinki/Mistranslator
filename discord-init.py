import discord, logging, re, os, json
from discord.ext import commands
import mistranslate as mt

#Initial setup
logging.basicConfig(level=logging.INFO)

__location__ = os.path.join(os.getcwd(),os.path.dirname(__file__))
conf_filepath = os.path.join(__location__, 'config.json')
config = None

try:
    cfgfile = open(conf_filepath)
    cfgjson = cfgfile.read()
    config = json.loads(cfgjson)
except FileNotFoundError:
    print("FATAL: 'config.json' file not found. Unable to log into Discord account. Exiting.")
    exit(1)

#Checking config for missing values
if 'errormsg-time' not in config:
    print("WARNING: Value 'errormsg-time' not found in config. Falling back to default error message lifetime of 120 seconds.")
    config['errormsg-time'] = 120

cmdbot = commands.Bot(command_prefix='mistl:')

async def send_parse_error(ctx,fullcmd,message):
    embed = discord.Embed(title='Parse Error',description="I can't figure out what you need from me! Did you mistype?",colour=0xff0000)
    embed.add_field(name='Command:',value=fullcmd)
    embed.add_field(name='Error:',value=message)
    await ctx.send(ctx.message.author.mention(),embed=embedmsg,delete_after=config['errormsg-time'])

@cmdbot.command()
async def translate(ctx, *args):
    fullmsg = ' '.join(args)
    
    #set up variables
    inputstr = None
    
    flags = {}
    mode = 0
    langlist = None
    
    #Check arguments
    while args:
        curarg = args.pop(0)
        #Check flag
        if curarg.startswith('-'):
            #Disallow composite arguments
            if len(curarg) > 2:
                await send_parse_error(fullmsg,'Composite flags (i.e. flags with multiple option tags in one, like -vd) are not allowed.')
                return
            #Warn about stray dashes/blank options
            elif len(curarg) == 1:
                await send_parse_error(fullmsg,'Blank flags (i.e. lone dashes that are not part of the translation input) are not allowed as arguments.')
                return
            #Check for duplicate flag
            elif curarg in flags:
                await send_parse_error(fullmsg,f'Duplicate flag detected: `{curarg}`')
                return
            else:
                #Process the option flag
                #Check if flag requires input
                if re.fullmatch(r'-[iotlLs]'):
                    #Throw error if there's no more input
                    if not args:
                        await send_parse_error(fullmsg,f'Flag `{curarg}` requires input, but no further input was detected.')
                        return
                    else:
                        flags[curarg] = args.pop(0)
                else:
                    flags[curarg] = True
        else:
            #If there are no more flags, treat the rest of the input as the text to translate
            inputstr = curarg + ' ' + ' '.join(args)
            break
        
    #TODO: Check for mutually exclusive flags
    if '-s' in flags and ('-o' in flags or '-t' in flags or '-l' in flags or '-L' in flags):
        pass
    
    #TODO: Start translation
    tlcl = mt.mt_Client()
    result = None
    try:
        result = tlcl.chain_translate(inputstr,mode,flags.get('-o',None),flags.get('-t',None),flags.get('-i',None),langlist)
    except (TypeError,ValueError):
        pass
    finally:
        pass

#TODO: Help function, standalone language detection, about

class BotClient(discord.Client):
    async def on_ready(self):
        print('Login successful. User ID: {0}'.format(self.user))
        
client = BotClient()
client.run(config['discord-auth-token'])
