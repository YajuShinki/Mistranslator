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

#custom functions
async def send_parse_error(ctx,fullcmd,message):
    embed = discord.Embed(title='Parse Error',description="I can't make sense of this command. Did you mistype?",colour=0xff0000)
    embed.add_field(name=fullcmd,value=message)
    await ctx.send(ctx.author.mention,embed=embed,delete_after=config['errormsg-time'])
    
async def send_value_error(ctx,fullcmd,message):
    embed = discord.Embed(title='Value Error',description="One or more values you put in are the wrong type.",colour=0xff0000)
    embed.add_field(name=fullcmd,value=message)
    await ctx.send(ctx.author.mention,embed=embed,delete_after=config['errormsg-time'])
    

    
#Command parser
cmdbot = commands.Bot(command_prefix='mistl:')

@cmdbot.command()
async def test(ctx):
    print(ctx.message)
    await ctx.send(ctx.author.mention+' Test Command')

@cmdbot.command()
async def translate(ctx, *args):
    args = list(args)
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
                await send_parse_error(ctx,fullmsg,'Composite flags (i.e. flags with multiple option tags in one, like -vd) are not allowed.')
                return
            #Warn about stray dashes/blank options
            elif len(curarg) == 1:
                await send_parse_error(ctx,fullmsg,'Blank flags (i.e. lone dashes that are not part of the translation input) are not allowed as arguments.')
                return
            #Check for duplicate flag
            elif curarg in flags:
                await send_parse_error(ctx,fullmsg,f'Duplicate flag detected: `{curarg}`')
                return
            else:
                #Process the option flag
                #Check if flag requires input
                if curarg[1] in ('i','o','t','l','L','s'):
                    #Throw error if there's no more input
                    if not args:
                        await send_parse_error(ctx,fullmsg,f'Flag `{curarg}` requires input, but no further input was detected.')
                        return
                    else:
                        flags[curarg] = args.pop(0)
                else:
                    flags[curarg] = True
        else:
            #If there are no more flags, treat the rest of the input as the text to translate
            inputstr = curarg + ' ' + ' '.join(args)
            break
    
    print(f"\nSENDER: {ctx.message.author.name}\nINPUT: {inputstr}\nFLAGS: {flags}\n")
    #TODO: Check for mutually exclusive flags
    #if '-s' in flags and ('-o' in flags or '-t' in flags or '-l' in flags or '-L' in flags):
        #pass
    
    #TODO: Start translation
    '''tlcl = mt.mt_Client()
    result = None
    try:
        result = tlcl.chain_translate(inputstr,mode,flags.get('-o',None),flags.get('-t',None),flags.get('-i',None),langlist)
    except (TypeError,ValueError):
        pass
    finally:
        pass'''

#TODO: Help function, standalone language detection, about

@cmdbot.event
async def on_ready():
    print('Login successful. Username: {0}'.format(cmdbot.user.name))

cmdbot.run(config['discord-auth-token'])
